from neo4j import Driver

from .models import (
    GameVehicle,
    NamedEntity,
    VehicleOption,
)


class VehicleNotFoundError(Exception):
    pass


class Neo4jVehicleRepository:
    def __init__(
        self,
        driver: Driver,
        database: str = "neo4j",
    ):
        self._driver = driver
        self._database = database

    def get_vehicle(
        self,
        vehicle_id: str,
    ) -> GameVehicle:
        query = """
        // =====================================================
        // Case 1: Version is the guessable car
        // =====================================================

        MATCH (version:Version {id: $vehicle_id})
        MATCH (variant:Variant)-[:HAS_VERSION]->(version)
        MATCH (model:Model)-[:HAS_VARIANT]->(variant)
        MATCH (manufacturer:Manufacturer)-[:PRODUCES]->(model)

        OPTIONAL MATCH
            (variant)-[:HAS_BODY_STYLE]->(body_style:BodyStyle)

        OPTIONAL MATCH
            (variant)-[:HAS_CLASS]->(vehicle_class:VehicleClass)

        OPTIONAL MATCH
            (variant)-[:HAS_DRIVETRAIN]->(drivetrain:Drivetrain)

        // Exact-engine usage:
        //
        // Version -> Engine
        // EngineFamily -> Engine
        // EngineSeries -> EngineFamily
        OPTIONAL MATCH
            (version)-[:USES_ENGINE]->(specific_engine:Engine)

        OPTIONAL MATCH
            (specific_engine)<-[:HAS_ENGINE]-(exact_engine_family:EngineFamily)

        OPTIONAL MATCH
            (exact_engine_family)<-[:HAS_ENGINE_FAMILY]-(exact_engine_series:EngineSeries)

        // Family-only usage:
        //
        // Version -> EngineFamily
        // EngineSeries -> EngineFamily
        OPTIONAL MATCH
            (version)-[:USES_ENGINE_FAMILY]->(direct_engine_family:EngineFamily)

        OPTIONAL MATCH
            (direct_engine_family)<-[:HAS_ENGINE_FAMILY]-(direct_engine_series:EngineSeries)

        OPTIONAL MATCH
            (variant)-[:SUCCEEDED_BY]->(successor:Variant)

        OPTIONAL MATCH
            (predecessor:Variant)-[:SUCCEEDED_BY]->(variant)

        RETURN
            version.id AS vehicle_id,

            manufacturer {
                .id,
                .name
            } AS manufacturer,

            model {
                .id,
                .name
            } AS model,

            variant {
                .id,
                .name
            } AS variant,

            version {
                .id,
                .name
            } AS version,

            variant.production_start AS production_start,
            variant.production_end AS production_end,
            version.power_hp AS power_hp,

            collect(
                DISTINCT body_style {
                    .id,
                    .name
                }
            ) AS body_styles,

            collect(
                DISTINCT vehicle_class {
                    .id,
                    .name
                }
            ) AS vehicle_classes,

            collect(
                DISTINCT drivetrain {
                    .id,
                    .name
                }
            ) AS drivetrains,

            collect(
                DISTINCT exact_engine_series {
                    .id,
                    .name
                }
            )
            +
            collect(
                DISTINCT direct_engine_series {
                    .id,
                    .name
                }
            ) AS engine_series,

            collect(
                DISTINCT exact_engine_family {
                    .id,
                    .name
                }
            )
            +
            collect(
                DISTINCT direct_engine_family {
                    .id,
                    .name
                }
            ) AS engine_families,

            collect(
                DISTINCT CASE
                    WHEN specific_engine IS NULL
                    THEN null
                    ELSE {
                        id: specific_engine.id,
                        name: specific_engine.code
                    }
                END
            ) AS engines,

            collect(
                DISTINCT CASE
                    WHEN specific_engine IS NULL
                    THEN null
                    ELSE {
                        id: specific_engine.id,
                        name: specific_engine.code
                    }
                END
            )
            +
            collect(
                DISTINCT direct_engine_family {
                    .id,
                    .name
                }
            ) AS engine_labels,

            collect(DISTINCT successor.id)
            +
            collect(DISTINCT predecessor.id)
                AS lineage_neighbor_ids


        UNION ALL


        // =====================================================
        // Case 2: Variant is guessable because it has no Version
        // =====================================================

        MATCH (variant:Variant {id: $vehicle_id})

        WHERE NOT EXISTS {
            MATCH (variant)-[:HAS_VERSION]->(:Version)
        }

        MATCH (model:Model)-[:HAS_VARIANT]->(variant)
        MATCH (manufacturer:Manufacturer)-[:PRODUCES]->(model)

        OPTIONAL MATCH
            (variant)-[:HAS_BODY_STYLE]->(body_style:BodyStyle)

        OPTIONAL MATCH
            (variant)-[:HAS_CLASS]->(vehicle_class:VehicleClass)

        OPTIONAL MATCH
            (variant)-[:HAS_DRIVETRAIN]->(drivetrain:Drivetrain)

        OPTIONAL MATCH
            (variant)-[:SUCCEEDED_BY]->(successor:Variant)

        OPTIONAL MATCH
            (predecessor:Variant)-[:SUCCEEDED_BY]->(variant)

        RETURN
            variant.id AS vehicle_id,

            manufacturer {
                .id,
                .name
            } AS manufacturer,

            model {
                .id,
                .name
            } AS model,

            variant {
                .id,
                .name
            } AS variant,

            null AS version,

            variant.production_start AS production_start,
            variant.production_end AS production_end,
            variant.power_hp AS power_hp,

            collect(
                DISTINCT body_style {
                    .id,
                    .name
                }
            ) AS body_styles,

            collect(
                DISTINCT vehicle_class {
                    .id,
                    .name
                }
            ) AS vehicle_classes,

            collect(
                DISTINCT drivetrain {
                    .id,
                    .name
                }
            ) AS drivetrains,

            [] AS engine_series,
            [] AS engine_families,
            [] AS engines,
            [] AS engine_labels,

            collect(DISTINCT successor.id)
            +
            collect(DISTINCT predecessor.id)
                AS lineage_neighbor_ids
        """

        records, _, _ = self._driver.execute_query(
            query,
            vehicle_id=vehicle_id,
            database_=self._database,
        )

        if not records:
            raise VehicleNotFoundError(
                f"Vehicle '{vehicle_id}' was not found."
            )

        row = records[0]

        model = self._to_named_entity(
            row["model"]
        )

        if (
            model is not None
            and model.name == "No Model"
        ):
            model = None

        return GameVehicle(
            id=row["vehicle_id"],

            manufacturer=self._to_named_entity(
                row["manufacturer"]
            ),

            model=model,

            variant=self._to_named_entity(
                row["variant"]
            ),

            version=self._to_named_entity(
                row["version"]
            ),

            production_start=row["production_start"],
            production_end=row["production_end"],
            power_hp=row["power_hp"],

            vehicle_classes=self._to_named_entity_set(
                row["vehicle_classes"]
            ),

            body_styles=self._to_named_entity_set(
                row["body_styles"]
            ),

            engine_families=self._to_named_entity_set(
                row["engine_families"]
            ),

            drivetrains=self._to_named_entity_set(
                row["drivetrains"]
            ),

            lineage_neighbor_ids=frozenset(
                value
                for value in row["lineage_neighbor_ids"]
                if value is not None
            ),

            engine_series=self._to_named_entity_set(
                row["engine_series"]
            ),

            engines=self._to_named_entity_set(
                row["engines"]
            ),

            engine_labels=self._to_named_entity_set(
                row["engine_labels"]
            ),
        )

    @staticmethod
    def _to_named_entity(
        value: dict | None,
    ) -> NamedEntity | None:
        if value is None:
            return None

        return NamedEntity(
            id=value["id"],
            name=value["name"],
        )

    @classmethod
    def _to_named_entity_set(
        cls,
        values: list[dict | None],
    ) -> frozenset[NamedEntity]:
        return frozenset(
            entity
            for value in values
            if value is not None
            if (entity := cls._to_named_entity(value))
            is not None
        )

    def list_guessable_vehicles(
        self,
    ) -> list[VehicleOption]:
        query = """
        CALL () {
            // Normal guessable cars: Versions
            MATCH (manufacturer:Manufacturer)
                -[:PRODUCES]->(model:Model)
                -[:HAS_VARIANT]->(variant:Variant)
                -[:HAS_VERSION]->(version:Version)

            RETURN
                version.id AS vehicle_id,
                manufacturer.name AS manufacturer_name,
                model.name AS model_name,
                variant.name AS variant_name,
                version.name AS version_name

            UNION ALL

            // Variant-only guessable cars
            MATCH (manufacturer:Manufacturer)
                -[:PRODUCES]->(model:Model)
                -[:HAS_VARIANT]->(variant:Variant)

            WHERE NOT EXISTS {
                MATCH (variant)-[:HAS_VERSION]->(:Version)
            }

            RETURN
                variant.id AS vehicle_id,
                manufacturer.name AS manufacturer_name,
                model.name AS model_name,
                variant.name AS variant_name,
                null AS version_name
        }

        RETURN
            vehicle_id,
            manufacturer_name,
            model_name,
            variant_name,
            version_name

        ORDER BY
            manufacturer_name,
            model_name,
            variant_name,
            version_name
        """

        records, _, _ = self._driver.execute_query(
            query,
            database_=self._database,
        )

        result = []

        for row in records:
            parts = [
                row["manufacturer_name"],
            ]

            if row["model_name"] != "No Model":
                parts.append(row["model_name"])

            parts.append(row["variant_name"])

            if row["version_name"] is not None:
                parts.append(row["version_name"])

            result.append(
                VehicleOption(
                    id=row["vehicle_id"],
                    display_name=" ".join(parts),
                )
            )

        return result

    def search_vehicles(
        self,
        search_text: str,
    ) -> list[VehicleOption]:
        search_text = search_text.strip().lower()

        if not search_text:
            return []

        vehicles = self.list_guessable_vehicles()

        matches = [
            vehicle
            for vehicle in vehicles
            if search_text in vehicle.display_name.lower()
        ]

        def rank(vehicle: VehicleOption) -> tuple:
            name = vehicle.display_name.lower()

            return (
                0 if name == search_text else 1,
                0 if name.endswith(search_text) else 1,
                0 if search_text in name.split() else 1,
                name,
            )

        matches.sort(
            key=rank,
        )

        return matches