def validate_canonical_dataset(
    dataset: dict,
) -> None:
    """
    Validate the globally merged Cardle canonical dataset.

    Raises ValueError containing all discovered validation
    errors.
    """

    errors = []

    collection_names = (
        "manufacturers",
        "models",
        "variants",
        "versions",
        "engine_series",
        "engine_families",
        "engines",
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
                f"Missing top-level collection: "
                f"{collection_name!r}"
            )

        elif not isinstance(
            dataset[collection_name],
            list,
        ):
            errors.append(
                f"Top-level collection "
                f"{collection_name!r} must be a list."
            )

    # Stop here if the structure is too broken to
    # validate safely.
    if errors:
        raise ValueError(
            _format_errors(errors)
        )

    # ---------------------------------------------------------
    # 2. Build ID registries and detect duplicate IDs
    # ---------------------------------------------------------

    registries = {}

    for collection_name in collection_names:
        registries[collection_name] = (
            _build_registry(
                dataset[collection_name],
                collection_name,
                errors,
            )
        )

    manufacturers = registries[
        "manufacturers"
    ]
    models = registries[
        "models"
    ]
    variants = registries[
        "variants"
    ]
    versions = registries[
        "versions"
    ]

    engine_series = registries[
        "engine_series"
    ]
    engine_families = registries[
        "engine_families"
    ]
    engines = registries[
        "engines"
    ]

    body_styles = registries[
        "body_styles"
    ]
    vehicle_classes = registries[
        "vehicle_classes"
    ]
    engine_positions = registries[
        "engine_positions"
    ]
    drivetrains = registries[
        "drivetrains"
    ]
    designers = registries[
        "designers"
    ]

    # ---------------------------------------------------------
    # 3. Models
    # ---------------------------------------------------------

    for model in dataset["models"]:
        current_model_id = model.get(
            "id"
        )

        manufacturer_id = model.get(
            "manufacturer_id"
        )

        if manufacturer_id not in manufacturers:
            errors.append(
                f"Model {current_model_id!r} refers to "
                f"nonexistent manufacturer "
                f"{manufacturer_id!r}."
            )

    # ---------------------------------------------------------
    # 4. Variants
    # ---------------------------------------------------------

    for variant in dataset["variants"]:
        current_variant_id = variant.get(
            "id"
        )

        model_id = variant.get(
            "model_id"
        )

        if model_id not in models:
            errors.append(
                f"Variant {current_variant_id!r} refers "
                f"to nonexistent model {model_id!r}."
            )

        _validate_reference_list(
            entity_id=current_variant_id,
            field_name="body_style_ids",
            ids=variant.get(
                "body_style_ids",
                [],
            ),
            target_registry=body_styles,
            target_name="body style",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=current_variant_id,
            field_name="vehicle_class_ids",
            ids=variant.get(
                "vehicle_class_ids",
                [],
            ),
            target_registry=vehicle_classes,
            target_name="vehicle class",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=current_variant_id,
            field_name="engine_position_ids",
            ids=variant.get(
                "engine_position_ids",
                [],
            ),
            target_registry=engine_positions,
            target_name="engine position",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=current_variant_id,
            field_name="drivetrain_ids",
            ids=variant.get(
                "drivetrain_ids",
                [],
            ),
            target_registry=drivetrains,
            target_name="drivetrain",
            errors=errors,
        )

        _validate_reference_list(
            entity_id=current_variant_id,
            field_name="designer_ids",
            ids=variant.get(
                "designer_ids",
                [],
            ),
            target_registry=designers,
            target_name="designer",
            errors=errors,
        )

        production_start = variant.get(
            "production_start"
        )

        production_end = variant.get(
            "production_end"
        )

        if (
            production_start is not None
            and production_end is not None
            and production_start > production_end
        ):
            errors.append(
                f"Variant {current_variant_id!r} has "
                f"production_start {production_start} "
                f"after production_end "
                f"{production_end}."
            )

        # predecessor/successor may legitimately remain
        # unresolved when their target vehicle is not in
        # the current dataset.

        _validate_relationships(
            current_variant_id,
            "predecessors",
            variant.get(
                "predecessors",
                [],
            ),
            variants,
            errors,
        )

        _validate_relationships(
            current_variant_id,
            "successors",
            variant.get(
                "successors",
                [],
            ),
            variants,
            errors,
        )

    # ---------------------------------------------------------
    # 5. EngineSeries
    # ---------------------------------------------------------

    for series in dataset[
        "engine_series"
    ]:
        series_id = series.get(
            "id"
        )

        manufacturer_id = series.get(
            "manufacturer_id"
        )

        if manufacturer_id not in manufacturers:
            errors.append(
                f"Engine series {series_id!r} refers "
                f"to nonexistent manufacturer "
                f"{manufacturer_id!r}."
            )

        if not series.get("name"):
            errors.append(
                f"Engine series {series_id!r} has no "
                f"valid name."
            )

    # ---------------------------------------------------------
    # 6. EngineFamily
    # ---------------------------------------------------------

    for engine_family in dataset[
        "engine_families"
    ]:
        engine_family_id = (
            engine_family.get("id")
        )

        engine_series_id = (
            engine_family.get(
                "engine_series_id"
            )
        )

        if (
            engine_series_id is not None
            and engine_series_id
            not in engine_series
        ):
            errors.append(
                f"Engine family "
                f"{engine_family_id!r} refers to "
                f"nonexistent engine series "
                f"{engine_series_id!r}."
            )

        if not engine_family.get("name"):
            errors.append(
                f"Engine family "
                f"{engine_family_id!r} has no valid "
                f"name."
            )

    # ---------------------------------------------------------
    # 7. Specific Engines
    # ---------------------------------------------------------

    for engine in dataset[
        "engines"
    ]:
        engine_id = engine.get(
            "id"
        )

        engine_family_id = engine.get(
            "engine_family_id"
        )

        # A specific engine is allowed to have no resolved
        # family.
        #
        # This is important for manufacturers whose naming
        # convention we do not yet understand.
        if (
            engine_family_id is not None
            and engine_family_id
            not in engine_families
        ):
            errors.append(
                f"Engine {engine_id!r} refers to "
                f"nonexistent engine family "
                f"{engine_family_id!r}."
            )

        if not engine.get("code"):
            errors.append(
                f"Engine {engine_id!r} has no valid "
                f"engine code."
            )

    # ---------------------------------------------------------
    # 8. Versions
    # ---------------------------------------------------------

    for version in dataset[
        "versions"
    ]:
        version_id = version.get(
            "id"
        )

        variant_id = version.get(
            "variant_id"
        )

        if variant_id not in variants:
            errors.append(
                f"Version {version_id!r} refers to "
                f"nonexistent variant "
                f"{variant_id!r}."
            )

        # =====================================================
        # Power
        # =====================================================

        power_hp = version.get(
            "power_hp"
        )

        if power_hp is not None:
            if not isinstance(
                power_hp,
                int,
            ):
                errors.append(
                    f"Version {version_id!r} has "
                    f"non-integer power_hp "
                    f"{power_hp!r}."
                )

            elif power_hp <= 0:
                errors.append(
                    f"Version {version_id!r} has "
                    f"invalid power_hp "
                    f"{power_hp!r}."
                )

        # =====================================================
        # Engine usages
        # =====================================================

        seen_engine_usages = set()

        for engine_usage in version.get(
            "engines",
            [],
        ):
            series_id = engine_usage.get(
                "engine_series_id"
            )

            family_id = engine_usage.get(
                "engine_family_id"
            )

            engine_id = engine_usage.get(
                "engine_id"
            )

            # -------------------------------------------------
            # A parsed engine usage must contain at least some
            # engine identity.
            #
            # BMW family-only source:
            #
            #     series = bmw_b
            #     family = bmw_b48
            #     engine = None
            #
            # Unknown manufacturer:
            #
            #     series = None
            #     family = None
            #     engine = exact code
            #
            # Both are valid.
            # -------------------------------------------------

            if (
                series_id is None
                and family_id is None
                and engine_id is None
            ):
                errors.append(
                    f"Version {version_id!r} contains "
                    f"an engine usage with no engine "
                    f"identity."
                )

            # -------------------------------------------------
            # References
            # -------------------------------------------------

            if (
                series_id is not None
                and series_id not in engine_series
            ):
                errors.append(
                    f"Version {version_id!r} refers to "
                    f"nonexistent engine series "
                    f"{series_id!r}."
                )

            if (
                family_id is not None
                and family_id
                not in engine_families
            ):
                errors.append(
                    f"Version {version_id!r} refers to "
                    f"nonexistent engine family "
                    f"{family_id!r}."
                )

            if (
                engine_id is not None
                and engine_id not in engines
            ):
                errors.append(
                    f"Version {version_id!r} refers to "
                    f"nonexistent engine "
                    f"{engine_id!r}."
                )

            # -------------------------------------------------
            # Ensure hierarchy stored on the usage agrees with
            # the global canonical entities.
            # -------------------------------------------------

            if (
                family_id is not None
                and family_id
                in engine_families
            ):
                family = engine_families[
                    family_id
                ]

                expected_series_id = (
                    family.get(
                        "engine_series_id"
                    )
                )

                if (
                    series_id
                    != expected_series_id
                ):
                    errors.append(
                        f"Version {version_id!r} engine "
                        f"usage has series "
                        f"{series_id!r}, but engine "
                        f"family {family_id!r} belongs "
                        f"to series "
                        f"{expected_series_id!r}."
                    )

            if (
                engine_id is not None
                and engine_id in engines
            ):
                engine = engines[
                    engine_id
                ]

                expected_family_id = (
                    engine.get(
                        "engine_family_id"
                    )
                )

                if (
                    family_id
                    != expected_family_id
                ):
                    errors.append(
                        f"Version {version_id!r} engine "
                        f"usage has family "
                        f"{family_id!r}, but engine "
                        f"{engine_id!r} belongs to "
                        f"family "
                        f"{expected_family_id!r}."
                    )

            # -------------------------------------------------
            # Displacement
            # -------------------------------------------------

            displacement_l = (
                engine_usage.get(
                    "displacement_l"
                )
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
                    f"Version {version_id!r} has "
                    f"invalid engine displacement "
                    f"{displacement_l!r}."
                )

            # -------------------------------------------------
            # Cylinder count
            # -------------------------------------------------

            cylinder_count = (
                engine_usage.get(
                    "cylinder_count"
                )
            )

            if cylinder_count is not None:
                if (
                    not isinstance(
                        cylinder_count,
                        int,
                    )
                    or cylinder_count <= 0
                ):
                    errors.append(
                        f"Version {version_id!r} has "
                        f"invalid engine cylinder_count "
                        f"{cylinder_count!r}."
                    )

            # -------------------------------------------------
            # Arrangement
            # -------------------------------------------------

            arrangement = engine_usage.get(
                "arrangement"
            )

            if (
                arrangement is not None
                and not isinstance(
                    arrangement,
                    str,
                )
            ):
                errors.append(
                    f"Version {version_id!r} has "
                    f"invalid engine arrangement "
                    f"{arrangement!r}."
                )

            # -------------------------------------------------
            # Duplicate usage
            #
            # engine_id must be included here.
            #
            # Two different specific engines can legitimately
            # belong to the same family and have the same
            # displacement.
            # -------------------------------------------------

            usage_key = (
                series_id,
                family_id,
                engine_id,
                displacement_l,
                cylinder_count,
                arrangement,
            )

            if (
                usage_key
                in seen_engine_usages
            ):
                errors.append(
                    f"Version {version_id!r} contains "
                    f"duplicate engine usage "
                    f"{usage_key!r}."
                )

            seen_engine_usages.add(
                usage_key
            )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    if errors:
        raise ValueError(
            _format_errors(errors)
        )


def _build_registry(
    entities: list[dict],
    collection_name: str,
    errors: list[str],
) -> dict:
    registry = {}

    for index, entity in enumerate(
        entities
    ):
        entity_id = entity.get(
            "id"
        )

        if not entity_id:
            errors.append(
                f"{collection_name}[{index}] "
                f"has no valid ID."
            )
            continue

        if entity_id in registry:
            errors.append(
                f"Duplicate ID {entity_id!r} "
                f"found in "
                f"{collection_name!r}."
            )
            continue

        registry[
            entity_id
        ] = entity

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
                f"Entity {entity_id!r} field "
                f"{field_name!r} refers to "
                f"nonexistent {target_name} "
                f"{target_id!r}."
            )

        if target_id in seen:
            errors.append(
                f"Entity {entity_id!r} field "
                f"{field_name!r} contains duplicate "
                f"reference {target_id!r}."
            )

        seen.add(
            target_id
        )


def _validate_relationships(
    variant_id: str,
    relationship_name: str,
    relationships: list[dict],
    variants: dict,
    errors: list[str],
) -> None:
    for relationship in relationships:
        target_id = relationship.get(
            "target_id"
        )

        # target_id=None is allowed.
        #
        # It simply means the referenced Variant has not yet
        # been resolved in this dataset.
        if target_id is None:
            continue

        if target_id not in variants:
            errors.append(
                f"Variant {variant_id!r} has "
                f"{relationship_name} reference to "
                f"nonexistent variant "
                f"{target_id!r}."
            )

        if target_id == variant_id:
            errors.append(
                f"Variant {variant_id!r} cannot "
                f"reference itself as a "
                f"{relationship_name}."
            )


def _format_errors(
    errors: list[str],
) -> str:
    lines = [
        f"Canonical dataset validation failed "
        f"with {len(errors)} error(s):"
    ]

    for error in errors:
        lines.append(
            f"  - {error}"
        )

    return "\n".join(
        lines
    )