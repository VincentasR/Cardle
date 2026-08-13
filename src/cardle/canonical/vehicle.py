from .body_styles import parse_body_styles
from .ids import (
    manufacturer_id,
    model_id,
    slugify,
    variant_id,
    version_id,
)
from .layouts import parse_layout
from .vehicle_classes import parse_vehicle_classes
from .years import parse_year_range
from .designers import parse_designers

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

    for variant_name in raw["variants"]:
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

        for predecessor_entry in raw.get("variant_predecessors", []):
            if predecessor_entry["variant"] == variant_name:
                predecessors.append(
                    {
                        "name": predecessor_entry.get("predecessor"),
                        "url": predecessor_entry.get("url"),
                        "target_id": None,
                    }
                )


        successors = []

        for successor_entry in raw.get("variant_successors", []):
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
            "source_url": raw["url"],
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

        for version_name in raw.get("versions", []):
            version = {
                "id": version_id(
                    manufacturer_name,
                    model_name,
                    variant_name,
                    version_name,
                ),
                "name": version_name,
            }

            variant["versions"].append(version)

        variants.append(variant)

    return {
        "manufacturer": manufacturer,
        "model": model,
        "variants": variants,
    }