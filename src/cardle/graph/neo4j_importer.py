from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence

from neo4j import GraphDatabase, Driver


BATCH_SIZE = 1000


EXPECTED_COLLECTIONS = {
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
}


# ---------------------------------------------------------------------
# CONSTRAINTS
# ---------------------------------------------------------------------

CONSTRAINTS = [
    """
    CREATE CONSTRAINT manufacturer_id_unique IF NOT EXISTS
    FOR (n:Manufacturer)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT model_id_unique IF NOT EXISTS
    FOR (n:Model)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT variant_id_unique IF NOT EXISTS
    FOR (n:Variant)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT version_id_unique IF NOT EXISTS
    FOR (n:Version)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT engine_family_id_unique IF NOT EXISTS
    FOR (n:EngineFamily)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT body_style_id_unique IF NOT EXISTS
    FOR (n:BodyStyle)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT vehicle_class_id_unique IF NOT EXISTS
    FOR (n:VehicleClass)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT engine_position_id_unique IF NOT EXISTS
    FOR (n:EnginePosition)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT drivetrain_id_unique IF NOT EXISTS
    FOR (n:Drivetrain)
    REQUIRE n.id IS UNIQUE
    """,
    """
    CREATE CONSTRAINT designer_id_unique IF NOT EXISTS
    FOR (n:Designer)
    REQUIRE n.id IS UNIQUE
    """,
]


# ---------------------------------------------------------------------
# NODE QUERIES
# ---------------------------------------------------------------------

NODE_QUERIES = {
    "manufacturers": """
        UNWIND $rows AS row

        MERGE (n:Manufacturer {id: row.id})
        SET n.name = row.name
    """,

    "models": """
        UNWIND $rows AS row

        MERGE (n:Model {id: row.id})
        SET n.name = row.name
    """,

    "variants": """
        UNWIND $rows AS row

        MERGE (n:Variant {id: row.id})
        SET n.name = row.name,
            n.source_url = row.source_url,
            n.production_start = row.production_start,
            n.production_end = row.production_end
    """,

    "versions": """
        UNWIND $rows AS row

        MERGE (n:Version {id: row.id})
        SET n.name = row.name,
            n.power_hp = row.power_hp
    """,

    "engine_families": """
        UNWIND $rows AS row

        MERGE (n:EngineFamily {id: row.id})
        SET n.name = row.name,
            n.cylinder_count = row.cylinder_count,
            n.arrangement = row.arrangement
    """,

    "body_styles": """
        UNWIND $rows AS row

        MERGE (n:BodyStyle {id: row.id})
        SET n.name = row.name
    """,

    "vehicle_classes": """
        UNWIND $rows AS row

        MERGE (n:VehicleClass {id: row.id})
        SET n.name = row.name
    """,

    "engine_positions": """
        UNWIND $rows AS row

        MERGE (n:EnginePosition {id: row.id})
        SET n.name = row.name
    """,

    "drivetrains": """
        UNWIND $rows AS row

        MERGE (n:Drivetrain {id: row.id})
        SET n.name = row.name
    """,

    "designers": """
        UNWIND $rows AS row

        MERGE (n:Designer {id: row.id})
        SET n.name = row.name
    """,
}


# ---------------------------------------------------------------------
# HIERARCHY
# ---------------------------------------------------------------------

MODEL_RELATIONSHIP_QUERY = """
    UNWIND $rows AS row

    MATCH (manufacturer:Manufacturer {id: row.manufacturer_id})
    MATCH (model:Model {id: row.id})

    MERGE (manufacturer)-[:PRODUCES]->(model)
"""


VARIANT_RELATIONSHIP_QUERY = """
    UNWIND $rows AS row

    MATCH (model:Model {id: row.model_id})
    MATCH (variant:Variant {id: row.id})

    MERGE (model)-[:HAS_VARIANT]->(variant)
"""


VERSION_RELATIONSHIP_QUERY = """
    UNWIND $rows AS row

    MATCH (variant:Variant {id: row.variant_id})
    MATCH (version:Version {id: row.id})

    MERGE (variant)-[:HAS_VERSION]->(version)
"""


# ---------------------------------------------------------------------
# VARIANT REFERENCE RELATIONSHIPS
# ---------------------------------------------------------------------

VARIANT_REFERENCE_RELATIONSHIPS = [
    ("body_style_ids", "BodyStyle", "HAS_BODY_STYLE"),
    ("vehicle_class_ids", "VehicleClass", "HAS_CLASS"),
    ("engine_position_ids", "EnginePosition", "HAS_ENGINE_POSITION"),
    ("drivetrain_ids", "Drivetrain", "HAS_DRIVETRAIN"),
    ("designer_ids", "Designer", "DESIGNED_BY"),
]


# ---------------------------------------------------------------------
# SUCCESSION
# ---------------------------------------------------------------------

SUCCESSOR_QUERY = """
    UNWIND $rows AS row

    MATCH (variant:Variant {id: row.id})

    UNWIND row.successors AS successor

    WITH variant, successor
    WHERE successor.target_id IS NOT NULL

    MATCH (target:Variant {id: successor.target_id})

    MERGE (variant)-[:SUCCEEDED_BY]->(target)
"""


PREDECESSOR_QUERY = """
    UNWIND $rows AS row

    MATCH (variant:Variant {id: row.id})

    UNWIND row.predecessors AS predecessor

    WITH variant, predecessor
    WHERE predecessor.target_id IS NOT NULL

    MATCH (target:Variant {id: predecessor.target_id})

    MERGE (target)-[:SUCCEEDED_BY]->(variant)
"""


# ---------------------------------------------------------------------
# ENGINE USAGE
# ---------------------------------------------------------------------

ENGINE_USAGE_QUERY = """
    UNWIND $rows AS row

    MATCH (version:Version {id: row.version_id})
    MATCH (engine:EngineFamily {id: row.engine_family_id})

    MERGE (
        version
    )-[usage:USES_ENGINE {usage_key: row.usage_key}]->(
        engine
    )

    SET usage.displacement_l = row.displacement_l
"""


# ---------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------

def load_canonical_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    missing = EXPECTED_COLLECTIONS - data.keys()

    if missing:
        raise ValueError(
            "Canonical JSON is missing required collections: "
            + ", ".join(sorted(missing))
        )

    return data


# ---------------------------------------------------------------------
# BATCHING
# ---------------------------------------------------------------------

def batches(
    rows: Sequence[dict[str, Any]],
    size: int = BATCH_SIZE,
) -> Iterable[Sequence[dict[str, Any]]]:

    for start in range(0, len(rows), size):
        yield rows[start:start + size]


def run_batched(
    driver: Driver,
    database: str,
    query: str,
    rows: Sequence[dict[str, Any]],
    batch_size: int = BATCH_SIZE,
) -> None:

    for batch in batches(rows, batch_size):
        driver.execute_query(
            query,
            rows=list(batch),
            database_=database,
        )


# ---------------------------------------------------------------------
# CONSTRAINT IMPORT
# ---------------------------------------------------------------------

def create_constraints(
    driver: Driver,
    database: str,
) -> None:

    for query in CONSTRAINTS:
        driver.execute_query(
            query,
            database_=database,
        )


# ---------------------------------------------------------------------
# NODE IMPORT
# ---------------------------------------------------------------------

def import_nodes(
    driver: Driver,
    database: str,
    data: dict[str, Any],
) -> None:

    for collection_name, query in NODE_QUERIES.items():

        rows = data[collection_name]

        run_batched(
            driver,
            database,
            query,
            rows,
        )

        print(
            f"Imported {len(rows):>4} "
            f"{collection_name}"
        )


# ---------------------------------------------------------------------
# VARIANT REFERENCES
# ---------------------------------------------------------------------

def variant_reference_query(
    id_field: str,
    target_label: str,
    relationship_type: str,
) -> str:

    # These values only come from the hard-coded constants above.
    return f"""
        UNWIND $rows AS row

        MATCH (variant:Variant {{id: row.id}})

        UNWIND row.{id_field} AS target_id

        MATCH (target:{target_label} {{id: target_id}})

        MERGE (variant)-[:{relationship_type}]->(target)
    """


# ---------------------------------------------------------------------
# ENGINE USAGE PREPARATION
# ---------------------------------------------------------------------

def build_engine_usage_rows(
    data: dict[str, Any],
) -> list[dict[str, Any]]:

    rows = []

    for version in data["versions"]:

        for engine in version["engines"]:

            displacement = engine.get("displacement_l")

            displacement_key = (
                "unknown"
                if displacement is None
                else str(displacement)
            )

            usage_key = (
                f"{version['id']}|"
                f"{engine['engine_family_id']}|"
                f"{displacement_key}"
            )

            rows.append(
                {
                    "version_id": version["id"],
                    "engine_family_id":
                        engine["engine_family_id"],
                    "displacement_l": displacement,
                    "usage_key": usage_key,
                }
            )

    return rows


# ---------------------------------------------------------------------
# RELATIONSHIP IMPORT
# ---------------------------------------------------------------------

def import_relationships(
    driver: Driver,
    database: str,
    data: dict[str, Any],
) -> None:

    # Manufacturer -> Model
    run_batched(
        driver,
        database,
        MODEL_RELATIONSHIP_QUERY,
        data["models"],
    )

    # Model -> Variant
    run_batched(
        driver,
        database,
        VARIANT_RELATIONSHIP_QUERY,
        data["variants"],
    )

    # Variant -> Version
    run_batched(
        driver,
        database,
        VERSION_RELATIONSHIP_QUERY,
        data["versions"],
    )

    # Variant descriptive relationships
    for (
        id_field,
        target_label,
        relationship_type,
    ) in VARIANT_REFERENCE_RELATIONSHIPS:

        query = variant_reference_query(
            id_field,
            target_label,
            relationship_type,
        )

        run_batched(
            driver,
            database,
            query,
            data["variants"],
        )

    # Variant succession
    run_batched(
        driver,
        database,
        SUCCESSOR_QUERY,
        data["variants"],
    )

    run_batched(
        driver,
        database,
        PREDECESSOR_QUERY,
        data["variants"],
    )

    # Version -> EngineFamily
    engine_usage_rows = build_engine_usage_rows(data)

    run_batched(
        driver,
        database,
        ENGINE_USAGE_QUERY,
        engine_usage_rows,
    )

    print(
        f"Imported {len(engine_usage_rows):>4} "
        f"engine usages"
    )


# ---------------------------------------------------------------------
# FULL IMPORT
# ---------------------------------------------------------------------

def import_graph(
    json_path: Path,
    uri: str,
    username: str,
    password: str,
    database: str,
) -> None:

    data = load_canonical_json(json_path)

    with GraphDatabase.driver(
        uri,
        auth=(username, password),
    ) as driver:

        driver.verify_connectivity()
        print("Connected to Neo4j.")

        create_constraints(
            driver,
            database,
        )

        print("Constraints ready.")

        import_nodes(
            driver,
            database,
            data,
        )

        import_relationships(
            driver,
            database,
            data,
        )

    print("Neo4j import complete.")


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Import Cardle canonical JSON into Neo4j."
        )
    )

    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to canonical JSON",
    )

    parser.add_argument(
        "--uri",
        default=os.getenv(
            "NEO4J_URI",
            "neo4j://localhost:7687",
        ),
    )

    parser.add_argument(
        "--username",
        default=os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        ),
    )

    parser.add_argument(
        "--password",
        default=os.getenv(
            "NEO4J_PASSWORD",
        ),
    )

    parser.add_argument(
        "--database",
        default=os.getenv(
            "NEO4J_DATABASE",
            "neo4j",
        ),
    )

    args = parser.parse_args()

    if not args.password:
        parser.error(
            "Neo4j password missing. "
            "Set NEO4J_PASSWORD or pass --password."
        )

    return args


def main() -> None:

    args = parse_args()

    import_graph(
        json_path=args.json_path,
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database,
    )


if __name__ == "__main__":
    main()