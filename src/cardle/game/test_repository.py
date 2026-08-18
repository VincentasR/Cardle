query = """
// =========================================================
// Case 1: normal guessable car = Version
// =========================================================

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


UNION ALL


// =========================================================
// Case 2: Variant with no Versions
// =========================================================

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
    (variant)-[:USES_ENGINE]->(engine:EngineFamily)

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