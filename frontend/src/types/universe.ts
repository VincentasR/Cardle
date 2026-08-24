export type UniverseNodeType =
    | 'manufacturer'
    | 'model'
    | 'variant'
    | 'version'
    | 'engine_family'

export type UniverseEdgeType =
    | 'hierarchy'
    | 'version'
    | 'engine'

export type UniverseNode = {
    id: string
    entity_id: string
    label: string
    type: UniverseNodeType

    manufacturer_id: string | null
    parent_model_id: string | null
    parent_variant_id: string | null

    production_start: number | null
    production_end: number | null

    vehicle_classes: string[]
    body_styles: string[]
    drivetrains: string[]

    power_hp: number | null
    engine_labels: string[]
}

export type UniverseEdge = {
    id: string
    source: string
    target: string
    type: UniverseEdgeType
}

export type UniverseGraph = {
    nodes: UniverseNode[]
    edges: UniverseEdge[]
}
