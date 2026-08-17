from neo4j import Driver

from .models import GameVehicle, NamedEntity


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

        OPTIONAL MATCH
            (version)-[:USES_ENGINE]->(engine:EngineFamily)

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
                DISTINCT engine {
                    .id,
                    .name
                }
            ) AS engine_families,

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

        model = self._to_named_entity(row["model"])

        if model is not None and model.name == "No Model":
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