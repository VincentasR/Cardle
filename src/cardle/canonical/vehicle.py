import re

from .body_styles import parse_body_styles
from .designers import parse_designers
from .engines import parse_engine_usage
from .ids import (
    manufacturer_id,
    model_id,
    slugify,
    variant_id,
    version_id,
)
from .layouts import parse_layout
from .power import parse_power_hp
from .vehicle_classes import parse_vehicle_classes
from .version_assignment import assign_versions_to_variant
from .years import parse_year_range


def clean_version_name(
    value: str,
) -> str:
    """
    Remove source/table annotation markers from a version name.

    Examples:
        "635d [ c ]" -> "635d"
        "320i [ a ]" -> "320i"
        "M35i xDrive *" -> "M35i xDrive"
        "M50 xDrive*" -> "M50 xDrive"
    """

    # Wikipedia-style bracketed references.
    value = re.sub(
        r"\s*\[\s*[^\]]+\s*\]\s*",
        " ",
        value,
    )

    # Trailing table/footnote markers.
    value = re.sub(
        r"\s*[*†‡]+\s*$",
        "",
        value,
    )

    return " ".join(
        value.split()
    )


def canonicalize_vehicle(
    raw: dict,
) -> dict:
    manufacturer_name = raw[
        "manufacturer"
    ]

    model_name = raw[
        "model"
    ]

    manufacturer = {
        "id": manufacturer_id(
            manufacturer_name
        ),
        "name": manufacturer_name,
    }

    model = {
        "id": model_id(
            manufacturer_name,
            model_name,
        ),
        "name": model_name,
    }

    variants = []

    # Deduplicated EngineFamily entities used by this
    # vehicle/page.
    canonical_engine_families = {}

    # --------------------------------------------------------
    # Build all Variant IDs represented by this Wikipedia page.
    #
    # This is used by the simplified Version-assignment layer.
    #
    # Most Versions remain shared between sibling Variants.
    # Only explicitly distinguishable cases such as BMW
    # long-wheelbase marketed Versions are separated.
    # --------------------------------------------------------

    page_variant_ids = [
        variant_id(
            manufacturer_name,
            model_name,
            variant_name,
        )
        for variant_name in raw.get(
            "variants",
            [],
        )
    ]

    for variant_name in raw.get(
        "variants",
        [],
    ):
        current_variant_id = variant_id(
            manufacturer_name,
            model_name,
            variant_name,
        )

        # ====================================================
        # Production period
        # ====================================================

        production_start = None
        production_end = None

        for production_entry in raw.get(
            "variant_production",
            [],
        ):
            if (
                production_entry.get(
                    "variant"
                )
                != variant_name
            ):
                continue

            (
                production_start,
                production_end,
            ) = parse_year_range(
                production_entry[
                    "production"
                ]
            )

            break

        # ====================================================
        # Body styles
        # ====================================================

        body_styles = []

        for body_style_entry in raw.get(
            "variant_body_styles",
            [],
        ):
            if (
                body_style_entry.get(
                    "variant"
                )
                != variant_name
            ):
                continue

            body_styles = (
                parse_body_styles(
                    body_style_entry[
                        "body_style"
                    ]
                )
            )

            break

        canonical_body_styles = [
            {
                "id": slugify(
                    body_style
                ),
                "name": body_style,
            }
            for body_style
            in body_styles
        ]

        # ====================================================
        # Vehicle classes
        # ====================================================

        vehicle_classes = []

        for vehicle_class_entry in raw.get(
            "variant_vehicle_classes",
            [],
        ):
            if (
                vehicle_class_entry.get(
                    "variant"
                )
                != variant_name
            ):
                continue

            vehicle_classes = (
                parse_vehicle_classes(
                    vehicle_class_entry[
                        "vehicle_class"
                    ]
                )
            )

            break

        canonical_vehicle_classes = [
            {
                "id": slugify(
                    vehicle_class
                ),
                "name": vehicle_class,
            }
            for vehicle_class
            in vehicle_classes
        ]

        # ====================================================
        # Layout
        # ====================================================

        engine_positions = []
        drivetrains = []

        for layout_entry in raw.get(
            "variant_layouts",
            [],
        ):
            if (
                layout_entry.get(
                    "variant"
                )
                != variant_name
            ):
                continue

            (
                engine_positions,
                drivetrains,
            ) = parse_layout(
                layout_entry[
                    "layout"
                ]
            )

            break

        canonical_engine_positions = [
            {
                "id": slugify(
                    engine_position
                ),
                "name": engine_position,
            }
            for engine_position
            in engine_positions
        ]

        canonical_drivetrains = [
            {
                "id": slugify(
                    drivetrain
                ),
                "name": drivetrain,
            }
            for drivetrain
            in drivetrains
        ]

        # ====================================================
        # Designers
        #
        # Unlike single-valued properties such as production
        # period or layout, one Variant can have multiple raw
        # designer records.
        #
        # Therefore we must collect ALL matching entries rather
        # than stopping after the first one.
        # ====================================================

        canonical_designers = []
        seen_designer_ids = set()

        for designer_entry in raw.get(
            "variant_designers",
            [],
        ):
            if (
                designer_entry.get(
                    "variant"
                )
                != variant_name
            ):
                continue

            raw_designer = (
                designer_entry.get(
                    "designer"
                )
            )

            if not raw_designer:
                continue

            designers = parse_designers(
                raw_designer
            )

            for designer in designers:
                designer_id = slugify(
                    designer
                )

                if not designer_id:
                    continue

                if (
                    designer_id
                    in seen_designer_ids
                ):
                    continue

                seen_designer_ids.add(
                    designer_id
                )

                canonical_designers.append(
                    {
                        "id": designer_id,
                        "name": designer,
                    }
                )

        # ====================================================
        # Predecessors
        # ====================================================

        predecessors = []

        for predecessor_entry in raw.get(
            "variant_predecessors",
            [],
        ):
            if (
                predecessor_entry.get(
                    "variant"
                )
                != variant_name
            ):
                continue

            predecessors.append(
                {
                    "name": (
                        predecessor_entry.get(
                            "predecessor"
                        )
                    ),
                    "url": (
                        predecessor_entry.get(
                            "url"
                        )
                    ),
                    "target_id": None,
                }
            )

        # ====================================================
        # Successors
        # ====================================================

        successors = []

        for successor_entry in raw.get(
            "variant_successors",
            [],
        ):
            if (
                successor_entry.get(
                    "variant"
                )
                != variant_name
            ):
                continue

            successors.append(
                {
                    "name": (
                        successor_entry.get(
                            "successor"
                        )
                    ),
                    "url": (
                        successor_entry.get(
                            "url"
                        )
                    ),
                    "target_id": None,
                }
            )

        # ====================================================
        # Variant
        # ====================================================

        variant = {
            "id": current_variant_id,
            "source_url": raw.get(
                "url"
            ),
            "name": variant_name,
            "production_start": (
                production_start
            ),
            "production_end": (
                production_end
            ),
            "body_styles": (
                canonical_body_styles
            ),
            "vehicle_classes": (
                canonical_vehicle_classes
            ),
            "engine_positions": (
                canonical_engine_positions
            ),
            "drivetrains": (
                canonical_drivetrains
            ),
            "designers": (
                canonical_designers
            ),
            "predecessors": (
                predecessors
            ),
            "successors": (
                successors
            ),
            "versions": [],
        }

        # ====================================================
        # Version assignment
        #
        # Wikipedia often provides one generation-wide Version
        # table for several sibling body-code Variants.
        #
        # We deliberately do NOT try to reconstruct exact
        # body-specific availability where the source does not
        # distinguish it.
        #
        # Generic Versions therefore remain shared.
        #
        # The assignment layer only separates explicitly
        # distinguishable cases, currently BMW LWB marketed
        # designations such as:
        #
        #     320Li
        #     320Ld
        #     740Le
        #
        # Importantly, each assignment retains the ORIGINAL raw
        # Version name so engine and power records can still be
        # matched correctly.
        # ====================================================

        version_assignments = (
            assign_versions_to_variant(
                raw_versions=raw.get(
                    "versions",
                    [],
                ),
                current_variant_id=(
                    current_variant_id
                ),
                page_variant_ids=(
                    page_variant_ids
                ),
            )
        )

        for version_assignment in (
            version_assignments
        ):
            raw_version_name = (
                version_assignment[
                    "raw_name"
                ]
            )

            version_name = (
                clean_version_name(
                    version_assignment[
                        "name"
                    ]
                )
            )

            if not version_name:
                continue

            # ================================================
            # Engines
            # ================================================

            engine_usages = []

            # Match engine records using the ORIGINAL raw
            # Version name.
            #
            # Example:
            #
            # raw:
            #     "318i / 320Li"
            #
            # canonical:
            #     G20 -> "318i"
            #     G28 -> "320Li"
            #
            # Engine extraction still stores:
            #
            #     version = "318i / 320Li"
            #
            # so raw_version_name must be used here.
            for engine_entry in raw.get(
                "version_engines",
                [],
            ):
                if (
                    engine_entry.get(
                        "version"
                    )
                    != raw_version_name
                ):
                    continue

                raw_engine = (
                    engine_entry.get(
                        "engine"
                    )
                )

                if not raw_engine:
                    continue

                (
                    engine_family,
                    engine_usage,
                ) = parse_engine_usage(
                    raw_engine
                )

                if (
                    engine_family is None
                    or engine_usage is None
                ):
                    continue

                canonical_engine_families[
                    engine_family["id"]
                ] = engine_family

                if (
                    engine_usage
                    not in engine_usages
                ):
                    engine_usages.append(
                        engine_usage
                    )

            # ================================================
            # Power
            # ================================================

            latest_power_hp = None

            # Again, match against the ORIGINAL raw Version
            # name.
            for power_entry in raw.get(
                "version_power",
                [],
            ):
                if (
                    power_entry.get(
                        "version"
                    )
                    != raw_version_name
                ):
                    continue

                raw_power = (
                    power_entry.get(
                        "power"
                    )
                )

                if not raw_power:
                    continue

                parsed_power = (
                    parse_power_hp(
                        raw_power
                    )
                )

                if (
                    parsed_power
                    is not None
                ):
                    latest_power_hp = (
                        parsed_power
                    )

            # ================================================
            # Version
            # ================================================

            version = {
                "id": version_id(
                    manufacturer_name,
                    model_name,
                    variant_name,
                    version_name,
                ),
                "name": version_name,
                "power_hp": (
                    latest_power_hp
                ),
                "engines": (
                    engine_usages
                ),
            }

            variant[
                "versions"
            ].append(
                version
            )

        variants.append(
            variant
        )

    return {
        "manufacturer": manufacturer,
        "model": model,
        "engine_families": list(
            canonical_engine_families.values()
        ),
        "variants": variants,
    }