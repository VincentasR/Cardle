from .relationships import resolve_relationships
from .vehicle import canonicalize_vehicle
from .validation import validate_canonical_dataset

def build_canonical_dataset(raw_vehicles: list[dict]) -> dict:
    """
    Convert raw scraped vehicle records into one globally
    consolidated and validated Cardle canonical dataset.
    """

    # 1. Canonicalize each Wikipedia page.
    canonical_pages = [
        canonicalize_vehicle(raw_vehicle)
        for raw_vehicle in raw_vehicles
    ]

    # 2. Resolve cross-page predecessor/successor relationships.
    canonical_pages = resolve_relationships(
        canonical_pages
    )

    # 3. Merge everything into one global Cardle dataset.
    dataset = _merge_canonical_pages(
        canonical_pages
    )

    # 4. Validate the final canonical dataset.
    validate_canonical_dataset(
        dataset
    )

    return dataset

def _merge_canonical_pages(canonical_pages: list[dict]) -> dict:
    manufacturers = {}
    models = {}

    engine_families = {}
    body_styles = {}
    vehicle_classes = {}
    engine_positions = {}
    drivetrains = {}
    designers = {}

    variants = {}
    versions = {}

    for page in canonical_pages:
        manufacturer = page["manufacturer"]

        _add_unique(
            manufacturers,
            manufacturer,
        )

        model = {
            **page["model"],
            "manufacturer_id": manufacturer["id"],
        }

        _add_unique(
            models,
            model,
        )

        for engine_family in page.get("engine_families", []):
            _merge_engine_family(
                engine_families,
                engine_family,
            )

        for variant in page.get("variants", []):
            body_style_ids = []

            for body_style in variant.get("body_styles", []):
                _add_unique(
                    body_styles,
                    body_style,
                )

                body_style_ids.append(
                    body_style["id"]
                )

            vehicle_class_ids = []

            for vehicle_class in variant.get(
                "vehicle_classes",
                [],
            ):
                _add_unique(
                    vehicle_classes,
                    vehicle_class,
                )

                vehicle_class_ids.append(
                    vehicle_class["id"]
                )

            engine_position_ids = []

            for engine_position in variant.get(
                "engine_positions",
                [],
            ):
                _add_unique(
                    engine_positions,
                    engine_position,
                )

                engine_position_ids.append(
                    engine_position["id"]
                )

            drivetrain_ids = []

            for drivetrain in variant.get(
                "drivetrains",
                [],
            ):
                _add_unique(
                    drivetrains,
                    drivetrain,
                )

                drivetrain_ids.append(
                    drivetrain["id"]
                )

            designer_ids = []

            for designer in variant.get("designers", []):
                _add_unique(
                    designers,
                    designer,
                )

                designer_ids.append(
                    designer["id"]
                )

            canonical_variant = {
                "id": variant["id"],
                "name": variant["name"],
                "model_id": page["model"]["id"],
                "source_url": variant.get("source_url"),
                "production_start": variant.get(
                    "production_start"
                ),
                "production_end": variant.get(
                    "production_end"
                ),
                "body_style_ids": body_style_ids,
                "vehicle_class_ids": vehicle_class_ids,
                "engine_position_ids": engine_position_ids,
                "drivetrain_ids": drivetrain_ids,
                "designer_ids": designer_ids,
                "predecessors": variant.get(
                    "predecessors",
                    [],
                ),
                "successors": variant.get(
                    "successors",
                    [],
                ),
            }

            _add_unique(
                variants,
                canonical_variant,
            )

            for version in variant.get("versions", []):
                canonical_version = {
                    "id": version["id"],
                    "name": version["name"],
                    "variant_id": variant["id"],
                    "power_hp": version.get("power_hp"),
                    "engines": version.get(
                        "engines",
                        [],
                    ),
                }

                _add_unique(
                    versions,
                    canonical_version,
                )

    return {
        "manufacturers": list(
            manufacturers.values()
        ),
        "models": list(
            models.values()
        ),
        "variants": list(
            variants.values()
        ),
        "versions": list(
            versions.values()
        ),
        "engine_families": list(
            engine_families.values()
        ),
        "body_styles": list(
            body_styles.values()
        ),
        "vehicle_classes": list(
            vehicle_classes.values()
        ),
        "engine_positions": list(
            engine_positions.values()
        ),
        "drivetrains": list(
            drivetrains.values()
        ),
        "designers": list(
            designers.values()
        ),
    }


def _add_unique(
    registry: dict,
    entity: dict,
) -> None:
    """
    Add an entity to a global registry using its canonical ID.

    If the same ID is encountered again with different data,
    raise an error rather than silently overwriting it.
    """

    entity_id = entity["id"]

    existing = registry.get(entity_id)

    if existing is None:
        registry[entity_id] = entity
        return

    if existing != entity:
        raise ValueError(
            f"Conflicting canonical entity for ID "
            f"{entity_id!r}:\n"
            f"existing={existing}\n"
            f"incoming={entity}"
        )


def _merge_engine_family(
    registry: dict,
    engine_family: dict,
) -> None:
    """
    Merge repeated EngineFamily entities.

    Missing properties may be filled by another page, but
    contradictory non-null properties cause an error.
    """

    engine_id = engine_family["id"]

    existing = registry.get(engine_id)

    if existing is None:
        registry[engine_id] = engine_family.copy()
        return

    if existing["name"] != engine_family["name"]:
        raise ValueError(
            f"Conflicting engine family names for "
            f"{engine_id!r}: "
            f"{existing['name']!r} vs "
            f"{engine_family['name']!r}"
        )

    for field in (
        "cylinder_count",
        "arrangement",
    ):
        old_value = existing.get(field)
        new_value = engine_family.get(field)

        if old_value is None and new_value is not None:
            existing[field] = new_value

        elif (
            old_value is not None
            and new_value is not None
            and old_value != new_value
        ):
            raise ValueError(
                f"Conflicting {field} for engine family "
                f"{engine_id!r}: "
                f"{old_value!r} vs {new_value!r}"
            )