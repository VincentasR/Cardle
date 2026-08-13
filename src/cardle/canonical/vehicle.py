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
from .years import parse_year_range


def clean_version_name(value: str) -> str:
    """
    Remove Wikipedia-style footnote markers from a version name.

    Examples:
        "635d [ c ]" -> "635d"
        "320i [ a ]" -> "320i"
        "GTI [ 1 ]" -> "GTI"
    """
    value = re.sub(
        r"\s*\[\s*[^\]]+\s*\]\s*",
        " ",
        value,
    )

    return " ".join(value.split())


def canonicalize_vehicle(raw: dict) -> dict:
    manufacturer_name = raw["manufacturer"]
    model_name = raw["model"]

    manufacturer = {
        "id": manufacturer_id(manufacturer_name),
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

    # Deduplicated EngineFamily entities used by this vehicle/page.
    canonical_engine_families = {}

    for variant_name in raw.get("variants", []):
        production_start = None
        production_end = None

        for production_entry in raw.get("variant_production", []):
            if production_entry["variant"] == variant_name:
                production_start, production_end = parse_year_range(
                    production_entry["production"]
                )
                break

        body_styles = []

        for body_style_entry in raw.get("variant_body_styles", []):
            if body_style_entry["variant"] == variant_name:
                body_styles = parse_body_styles(
                    body_style_entry["body_style"]
                )
                break

        canonical_body_styles = [
            {
                "id": slugify(body_style),
                "name": body_style,
            }
            for body_style in body_styles
        ]

        vehicle_classes = []

        for vehicle_class_entry in raw.get(
            "variant_vehicle_classes",
            [],
        ):
            if vehicle_class_entry["variant"] == variant_name:
                vehicle_classes = parse_vehicle_classes(
                    vehicle_class_entry["vehicle_class"]
                )
                break

        canonical_vehicle_classes = [
            {
                "id": slugify(vehicle_class),
                "name": vehicle_class,
            }
            for vehicle_class in vehicle_classes
        ]

        engine_positions = []
        drivetrains = []

        for layout_entry in raw.get("variant_layouts", []):
            if layout_entry["variant"] == variant_name:
                engine_positions, drivetrains = parse_layout(
                    layout_entry["layout"]
                )
                break

        canonical_engine_positions = [
            {
                "id": slugify(engine_position),
                "name": engine_position,
            }
            for engine_position in engine_positions
        ]

        canonical_drivetrains = [
            {
                "id": slugify(drivetrain),
                "name": drivetrain,
            }
            for drivetrain in drivetrains
        ]

        designers = []

        for designer_entry in raw.get("variant_designers", []):
            if designer_entry["variant"] == variant_name:
                designers = parse_designers(
                    designer_entry["designer"]
                )
                break

        canonical_designers = [
            {
                "id": slugify(designer),
                "name": designer,
            }
            for designer in designers
        ]

        predecessors = []

        for predecessor_entry in raw.get(
            "variant_predecessors",
            [],
        ):
            if predecessor_entry["variant"] == variant_name:
                predecessors.append(
                    {
                        "name": predecessor_entry.get("predecessor"),
                        "url": predecessor_entry.get("url"),
                        "target_id": None,
                    }
                )

        successors = []

        for successor_entry in raw.get(
            "variant_successors",
            [],
        ):
            if successor_entry["variant"] == variant_name:
                successors.append(
                    {
                        "name": successor_entry.get("successor"),
                        "url": successor_entry.get("url"),
                        "target_id": None,
                    }
                )

        variant = {
            "id": variant_id(
                manufacturer_name,
                model_name,
                variant_name,
            ),
            "source_url": raw.get("url"),
            "name": variant_name,
            "production_start": production_start,
            "production_end": production_end,
            "body_styles": canonical_body_styles,
            "vehicle_classes": canonical_vehicle_classes,
            "engine_positions": canonical_engine_positions,
            "drivetrains": canonical_drivetrains,
            "designers": canonical_designers,
            "predecessors": predecessors,
            "successors": successors,
            "versions": [],
        }

        for raw_version_name in raw.get("versions", []):
            # Cleaned value is only used for canonical output.
            version_name = clean_version_name(raw_version_name)

            engine_usages = []

            # Use the original raw name when matching raw records.
            for engine_entry in raw.get("version_engines", []):
                if engine_entry["version"] != raw_version_name:
                    continue

                engine_family, engine_usage = parse_engine_usage(
                    engine_entry["engine"]
                )

                if engine_family is None or engine_usage is None:
                    continue

                canonical_engine_families[
                    engine_family["id"]
                ] = engine_family

                if engine_usage not in engine_usages:
                    engine_usages.append(engine_usage)

            latest_power_hp = None

            # Again, match using the original raw version name.
            for power_entry in raw.get("version_power", []):
                if power_entry["version"] != raw_version_name:
                    continue

                parsed_power = parse_power_hp(
                    power_entry["power"]
                )

                if parsed_power is not None:
                    latest_power_hp = parsed_power

            version = {
                "id": version_id(
                    manufacturer_name,
                    model_name,
                    variant_name,
                    version_name,
                ),
                "name": version_name,
                "power_hp": latest_power_hp,
                "engines": engine_usages,
            }

            variant["versions"].append(version)

        variants.append(variant)

    return {
        "manufacturer": manufacturer,
        "model": model,
        "engine_families": list(
            canonical_engine_families.values()
        ),
        "variants": variants,
    }