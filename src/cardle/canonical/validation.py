def validate_canonical_dataset(dataset: dict) -> None:
    """
    Validate the globally merged Cardle canonical dataset.

    Raises ValueError containing all discovered validation errors.
    """

    errors = []

    collection_names = (
        "manufacturers",
        "models",
        "variants",
        "versions",
        "engine_families",
        "body_styles",
        "vehicle_classes",
        "engine_positions",
        "drivetrains",
        "designers",
    )

    # ---------------------------------------------------------
    # 1. Check that all expected collections exist
    # ---------------------------------------------------------

    for collection_name in collection_names:
        if collection_name not in dataset:
            errors.append(
                f"Missing top-level collection: {collection_name!r}"
            )

        elif not isinstance(dataset[collection_name], list):
            errors.append(
                f"Top-level collection {collection_name!r} "
                f"must be a list."
            )

    # Stop here if the structure is too broken to validate safely.
    if errors:
        raise ValueError(_format_errors(errors))

    # ---------------------------------------------------------
    # 2. Build ID registries and detect duplicate IDs
    # ---------------------------------------------------------

    registries = {}

    for collection_name in collection_names:
        registries[collection_name] = _build_registry(
            dataset[collection_name],
            collection_name,
            errors,
        )

    manufacturers = registries["manufacturers"]
    models = registries["models"]
    variants = registries["variants"]
    versions = registries["versions"]

    engine_families = registries["engine_families"]
    body_styles = registries["body_styles"]
    vehicle_classes = registries["vehicle_classes"]
    engine_positions = registries["engine_positions"]
    drivetrains = registries["drivetrains"]
    designers = registries["designers"]

    # ---------------------------------------------------------
    # 3. Models
    # ---------------------------------------------------------

    for model in dataset["models"]:
        model_id = model.get("id")
        manufacturer_id = model.get("manufacturer_id")

        if manufacturer_id not in manufacturers:
            errors.append(
                f"Model {model_id!r} refers to nonexistent "
                f"manufacturer {manufacturer_id!r}."
            )

    # ---------------------------------------------------------
    # 4. Variants
    # ---------------------------------------------------------

    for variant in dataset["variants"]:
        variant_id = variant.get("id")
        model_id = variant.get("model_id")

        if model_id not in models:
            errors.append(
                f"Variant {variant_id!r} refers to nonexistent "
                f"model {model_id!r}."
            )

        _validate_reference_list(
            entity_id=variant_id,
            field_name="body_style_ids",
            ids=variant.get("body_style_ids", []),
            target_registry=body_styles,
            target_name="body style",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=variant_id,
            field_name="vehicle_class_ids",
            ids=variant.get("vehicle_class_ids", []),
            target_registry=vehicle_classes,
            target_name="vehicle class",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=variant_id,
            field_name="engine_position_ids",
            ids=variant.get("engine_position_ids", []),
            target_registry=engine_positions,
            target_name="engine position",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=variant_id,
            field_name="drivetrain_ids",
            ids=variant.get("drivetrain_ids", []),
            target_registry=drivetrains,
            target_name="drivetrain",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=variant_id,
            field_name="designer_ids",
            ids=variant.get("designer_ids", []),
            target_registry=designers,
            target_name="designer",
            errors=errors,
        )

        production_start = variant.get("production_start")
        production_end = variant.get("production_end")

        if (
            production_start is not None
            and production_end is not None
            and production_start > production_end
        ):
            errors.append(
                f"Variant {variant_id!r} has production_start "
                f"{production_start} after production_end "
                f"{production_end}."
            )

        # predecessor/successor may legitimately be unresolved
        # when their target vehicle is not in the current dataset.
        _validate_relationships(
            variant_id,
            "predecessors",
            variant.get("predecessors", []),
            variants,
            errors,
        )

        _validate_relationships(
            variant_id,
            "successors",
            variant.get("successors", []),
            variants,
            errors,
        )

    # ---------------------------------------------------------
    # 5. Versions
    # ---------------------------------------------------------

    for version in dataset["versions"]:
        version_id = version.get("id")
        variant_id = version.get("variant_id")

        if variant_id not in variants:
            errors.append(
                f"Version {version_id!r} refers to nonexistent "
                f"variant {variant_id!r}."
            )

        power_hp = version.get("power_hp")

        if power_hp is not None:
            if not isinstance(power_hp, int):
                errors.append(
                    f"Version {version_id!r} has non-integer "
                    f"power_hp {power_hp!r}."
                )

            elif power_hp <= 0:
                errors.append(
                    f"Version {version_id!r} has invalid "
                    f"power_hp {power_hp!r}."
                )

        seen_engine_usages = set()

        for engine_usage in version.get("engines", []):
            engine_family_id = engine_usage.get(
                "engine_family_id"
            )

            if engine_family_id not in engine_families:
                errors.append(
                    f"Version {version_id!r} refers to "
                    f"nonexistent engine family "
                    f"{engine_family_id!r}."
                )

            displacement_l = engine_usage.get(
                "displacement_l"
            )

            if (
                displacement_l is not None
                and (
                    not isinstance(
                        displacement_l,
                        (int, float),
                    )
                    or displacement_l <= 0
                )
            ):
                errors.append(
                    f"Version {version_id!r} has invalid "
                    f"engine displacement "
                    f"{displacement_l!r}."
                )

            usage_key = (
                engine_family_id,
                displacement_l,
            )

            if usage_key in seen_engine_usages:
                errors.append(
                    f"Version {version_id!r} contains duplicate "
                    f"engine usage {usage_key!r}."
                )

            seen_engine_usages.add(usage_key)

    # ---------------------------------------------------------
    # 6. Engine families
    # ---------------------------------------------------------

    for engine_family in dataset["engine_families"]:
        engine_id = engine_family.get("id")
        cylinder_count = engine_family.get(
            "cylinder_count"
        )

        if cylinder_count is not None:
            if (
                not isinstance(cylinder_count, int)
                or cylinder_count <= 0
            ):
                errors.append(
                    f"Engine family {engine_id!r} has invalid "
                    f"cylinder_count {cylinder_count!r}."
                )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    if errors:
        raise ValueError(_format_errors(errors))


def _build_registry(
    entities: list[dict],
    collection_name: str,
    errors: list[str],
) -> dict:
    registry = {}

    for index, entity in enumerate(entities):
        entity_id = entity.get("id")

        if not entity_id:
            errors.append(
                f"{collection_name}[{index}] has no valid ID."
            )
            continue

        if entity_id in registry:
            errors.append(
                f"Duplicate ID {entity_id!r} found in "
                f"{collection_name!r}."
            )
            continue

        registry[entity_id] = entity

    return registry


def _validate_reference_list(
    entity_id: str,
    field_name: str,
    ids: list[str],
    target_registry: dict,
    target_name: str,
    errors: list[str],
) -> None:
    seen = set()

    for target_id in ids:
        if target_id not in target_registry:
            errors.append(
                f"Entity {entity_id!r} field {field_name!r} "
                f"refers to nonexistent {target_name} "
                f"{target_id!r}."
            )

        if target_id in seen:
            errors.append(
                f"Entity {entity_id!r} field {field_name!r} "
                f"contains duplicate reference "
                f"{target_id!r}."
            )

        seen.add(target_id)


def _validate_relationships(
    variant_id: str,
    relationship_name: str,
    relationships: list[dict],
    variants: dict,
    errors: list[str],
) -> None:
    for relationship in relationships:
        target_id = relationship.get("target_id")

        # target_id=None is allowed.
        # It simply means the referenced variant has not yet
        # been resolved in this dataset.
        if target_id is None:
            continue

        if target_id not in variants:
            errors.append(
                f"Variant {variant_id!r} has {relationship_name} "
                f"reference to nonexistent variant "
                f"{target_id!r}."
            )

        if target_id == variant_id:
            errors.append(
                f"Variant {variant_id!r} cannot reference itself "
                f"as a {relationship_name}."
            )


def _format_errors(errors: list[str]) -> str:
    lines = [
        f"Canonical dataset validation failed "
        f"with {len(errors)} error(s):"
    ]

    for error in errors:
        lines.append(
            f"  - {error}"
        )

    return "\n".join(lines)