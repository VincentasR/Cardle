from __future__ import annotations

from collections.abc import Sequence

from neo4j import Driver


class Neo4jUniverseRepository:
    """
    Read-only Neo4j repository for the Automotive Universe.

    The browser stores guessable vehicle IDs that the player has discovered.

    Universe progression is VARIANT-based:
    discovering any Version of a Variant unlocks the whole Variant, including
    every Version that belongs to it.

    Variant-only guessable vehicles work the same way: the Variant itself is
    unlocked even though it has no Version nodes.
    """

    def __init__(
        self,
        driver: Driver,
        database: str = "neo4j",
    ):
        self._driver = driver
        self._database = database

    def get_graph(
        self,
        unlocked_vehicle_ids: Sequence[str],
    ) -> tuple[list[dict], list[dict]]:
        vehicle_ids = list(
            dict.fromkeys(
                vehicle_id
                for vehicle_id in unlocked_vehicle_ids
                if vehicle_id
            )
        )

        if not vehicle_ids:
            return [], []

        query = """
        // =====================================================
        // 1. Convert every discovered guessable vehicle into its
        //    parent Variant.
        //
        //    If the discovered ID is a Version, unlock that
        //    Version's Variant.
        //
        //    If the discovered ID is already a Variant
        //    (a no-Version guessable vehicle), unlock it directly.
        // =====================================================

        UNWIND $vehicle_ids AS vehicle_id

        CALL {
            WITH vehicle_id

            MATCH (variant:Variant)-[:HAS_VERSION]->(
                version:Version {id: vehicle_id}
            )

            RETURN variant.id AS unlocked_variant_id

            UNION

            WITH vehicle_id

            MATCH (variant:Variant {id: vehicle_id})

            RETURN variant.id AS unlocked_variant_id
        }

        WITH DISTINCT unlocked_variant_id


        // =====================================================
        // 2. Reconstruct the complete unlocked Variant.
        //
        //    Important:
        //    once a Variant is unlocked, ALL of its Version nodes
        //    are returned, not only the Version that was guessed.
        // =====================================================

        MATCH (variant:Variant {id: unlocked_variant_id})
        MATCH (model:Model)-[:HAS_VARIANT]->(variant)
        MATCH (manufacturer:Manufacturer)-[:PRODUCES]->(model)

        OPTIONAL MATCH
            (variant)-[:HAS_BODY_STYLE]->(body_style:BodyStyle)

        OPTIONAL MATCH
            (variant)-[:HAS_CLASS]->(vehicle_class:VehicleClass)

        OPTIONAL MATCH
            (variant)-[:HAS_DRIVETRAIN]->(drivetrain:Drivetrain)

        OPTIONAL MATCH
            (variant)-[:HAS_VERSION]->(version:Version)

        OPTIONAL MATCH
            (version)-[:USES_ENGINE]->(specific_engine:Engine)

        OPTIONAL MATCH
            (specific_engine)<-[:HAS_ENGINE]-(specific_family:EngineFamily)

        OPTIONAL MATCH
            (version)-[:USES_ENGINE_FAMILY]->(direct_family:EngineFamily)

        RETURN
            manufacturer.id AS manufacturer_id,
            manufacturer.name AS manufacturer_name,

            model.id AS model_id,
            model.name AS model_name,

            variant.id AS variant_id,
            variant.name AS variant_name,
            variant.production_start AS production_start,
            variant.production_end AS production_end,

            version.id AS version_id,
            version.name AS version_name,
            version.power_hp AS power_hp,

            collect(DISTINCT body_style.name)
                AS body_styles,

            collect(DISTINCT vehicle_class.name)
                AS vehicle_classes,

            collect(DISTINCT drivetrain.name)
                AS drivetrains,

            collect(
                DISTINCT CASE
                    WHEN specific_family IS NULL
                    THEN null
                    ELSE {
                        id: specific_family.id,
                        name: specific_family.name
                    }
                END
            )
            +
            collect(
                DISTINCT CASE
                    WHEN direct_family IS NULL
                    THEN null
                    ELSE {
                        id: direct_family.id,
                        name: direct_family.name
                    }
                END
            ) AS engine_families,

            collect(DISTINCT specific_engine.code)
            +
            collect(DISTINCT direct_family.name)
                AS engine_labels

        ORDER BY
            manufacturer_name,
            model_name,
            variant_name,
            version_name
        """

        records, _, _ = self._driver.execute_query(
            query,
            vehicle_ids=vehicle_ids,
            database_=self._database,
        )

        nodes_by_id: dict[str, dict] = {}
        edges_by_id: dict[str, dict] = {}

        def graph_id(
            node_type: str,
            entity_id: str,
        ) -> str:
            return f"{node_type}:{entity_id}"

        def add_node(node: dict) -> None:
            nodes_by_id.setdefault(
                node["id"],
                node,
            )

        def add_edge(
            edge_id: str,
            source: str,
            target: str,
            edge_type: str,
        ) -> None:
            edges_by_id.setdefault(
                edge_id,
                {
                    "id": edge_id,
                    "source": source,
                    "target": target,
                    "type": edge_type,
                },
            )

        for row in records:
            manufacturer_node_id = graph_id(
                "manufacturer",
                row["manufacturer_id"],
            )

            add_node(
                {
                    "id": manufacturer_node_id,
                    "entity_id": row["manufacturer_id"],
                    "label": row["manufacturer_name"],
                    "type": "manufacturer",
                    "manufacturer_id": None,
                    "parent_model_id": None,
                    "parent_variant_id": None,
                    "production_start": None,
                    "production_end": None,
                    "vehicle_classes": [],
                    "body_styles": [],
                    "drivetrains": [],
                    "power_hp": None,
                    "engine_labels": [],
                }
            )

            # "No Model" is only a database placeholder.
            # The Universe displays these vehicles as:
            #
            #     Manufacturer -> Variant
            #
            # instead of:
            #
            #     Manufacturer -> No Model -> Variant
            has_real_model = (
                row["model_name"] != "No Model"
            )

            model_node_id: str | None = None

            if has_real_model:
                model_node_id = graph_id(
                    "model",
                    row["model_id"],
                )

                add_node(
                    {
                        "id": model_node_id,
                        "entity_id": row["model_id"],
                        "label": row["model_name"],
                        "type": "model",
                        "manufacturer_id": manufacturer_node_id,
                        "parent_model_id": None,
                        "parent_variant_id": None,
                        "production_start": None,
                        "production_end": None,
                        "vehicle_classes": [],
                        "body_styles": [],
                        "drivetrains": [],
                        "power_hp": None,
                        "engine_labels": [],
                    }
                )

                add_edge(
                    edge_id=(
                        f"hierarchy:"
                        f"{manufacturer_node_id}->{model_node_id}"
                    ),
                    source=manufacturer_node_id,
                    target=model_node_id,
                    edge_type="hierarchy",
                )

            variant_node_id = graph_id(
                "variant",
                row["variant_id"],
            )

            add_node(
                {
                    "id": variant_node_id,
                    "entity_id": row["variant_id"],
                    "label": row["variant_name"],
                    "type": "variant",
                    "manufacturer_id": manufacturer_node_id,
                    "parent_model_id": model_node_id,
                    "parent_variant_id": None,
                    "production_start": row["production_start"],
                    "production_end": row["production_end"],
                    "vehicle_classes": self._clean_strings(
                        row["vehicle_classes"]
                    ),
                    "body_styles": self._clean_strings(
                        row["body_styles"]
                    ),
                    "drivetrains": self._clean_strings(
                        row["drivetrains"]
                    ),
                    "power_hp": None,
                    "engine_labels": [],
                }
            )

            variant_parent_id = (
                model_node_id
                if model_node_id is not None
                else manufacturer_node_id
            )

            add_edge(
                edge_id=(
                    f"hierarchy:"
                    f"{variant_parent_id}->{variant_node_id}"
                ),
                source=variant_parent_id,
                target=variant_node_id,
                edge_type="hierarchy",
            )

            if row["version_id"] is None:
                continue

            version_node_id = graph_id(
                "version",
                row["version_id"],
            )

            add_node(
                {
                    "id": version_node_id,
                    "entity_id": row["version_id"],
                    "label": row["version_name"],
                    "type": "version",
                    "manufacturer_id": manufacturer_node_id,
                    "parent_model_id": model_node_id,
                    "parent_variant_id": variant_node_id,
                    "production_start": None,
                    "production_end": None,
                    "vehicle_classes": [],
                    "body_styles": [],
                    "drivetrains": [],
                    "power_hp": row["power_hp"],
                    "engine_labels": self._clean_strings(
                        row["engine_labels"]
                    ),
                }
            )

            add_edge(
                edge_id=(
                    f"version:"
                    f"{variant_node_id}->{version_node_id}"
                ),
                source=variant_node_id,
                target=version_node_id,
                edge_type="version",
            )

            for family in self._clean_entities(
                row["engine_families"]
            ):
                family_node_id = graph_id(
                    "engine_family",
                    family["id"],
                )

                add_node(
                    {
                        "id": family_node_id,
                        "entity_id": family["id"],
                        "label": family["name"],
                        "type": "engine_family",
                        "manufacturer_id": None,
                        "parent_model_id": None,
                        "parent_variant_id": None,
                        "production_start": None,
                        "production_end": None,
                        "vehicle_classes": [],
                        "body_styles": [],
                        "drivetrains": [],
                        "power_hp": None,
                        "engine_labels": [],
                    }
                )

                add_edge(
                    edge_id=(
                        f"engine:"
                        f"{version_node_id}->{family_node_id}"
                    ),
                    source=version_node_id,
                    target=family_node_id,
                    edge_type="engine",
                )

        nodes = sorted(
            nodes_by_id.values(),
            key=lambda node: (
                node["type"],
                node["label"].lower(),
                node["id"],
            ),
        )

        edges = sorted(
            edges_by_id.values(),
            key=lambda edge: edge["id"],
        )

        return nodes, edges

    @staticmethod
    def _clean_strings(
        values: list[str | None],
    ) -> list[str]:
        return sorted(
            {
                value
                for value in values
                if value is not None
            }
        )

    @staticmethod
    def _clean_entities(
        values: list[dict | None],
    ) -> list[dict]:
        result: dict[str, dict] = {}

        for value in values:
            if value is None:
                continue

            result[value["id"]] = {
                "id": value["id"],
                "name": value["name"],
            }

        return sorted(
            result.values(),
            key=lambda entity: (
                entity["name"].lower(),
                entity["id"],
            ),
        )