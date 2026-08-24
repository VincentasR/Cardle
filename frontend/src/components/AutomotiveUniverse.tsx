import {
    useEffect,
    useMemo,
    useRef,
    useState,
} from 'react'

import cytoscape, {
    type Core,
    type ElementDefinition,
    type NodeSingular,
} from 'cytoscape'

import type {
    UniverseGraph,
    UniverseNode,
} from '../types/universe'


type AutomotiveUniverseProps = {
    unlockedVehicleIds: string[]
    newlyUnlockedVehicleId: string | null
    onUnlockAnimationComplete: (
        vehicleId: string,
    ) => void
}

type Point = {
    x: number
    y: number
}

type InfoRow = {
    label: string
    value: string
}

type NodeInfo = {
    type: string
    title: string
    subtitle?: string
    rows: InfoRow[]
}

type ShortestRoute = {
    nodeIds: string[]
    edgeIds: string[]
}

type GraphActions = {
    fitVisible: () => void
    centerSelected: (
        nodeId: string,
    ) => void
    showBaseUniverse: () => void
    showAllVersions: () => void
    showAllConnections: () => void
    clearConnectionView: () => void
}

const VERSION_DISTANCE = 165
const VERSION_RADIAL_GAP = 96
const VERSION_LANE_WOBBLE = 12
const NODE_GAP = 14
const MAX_SHORTEST_ROUTES = 50

const VERSION_EXPAND_DURATION = 270
const VERSION_COLLAPSE_DURATION = 190
const CONNECTION_REVEAL_DURATION = 310
const REVEAL_STAGGER = 24
const UNLOCK_PULSE_DURATION = 1850

const CENTER_LAYOUT_DURATION = 420
const CENTER_RING_GAP = 220
const CENTER_MIN_NODE_ARC = 112


function prefersReducedMotion(): boolean {
    return window.matchMedia(
        '(prefers-reduced-motion: reduce)',
    ).matches
}


function polar(
    center: Point,
    radius: number,
    angleDegrees: number,
): Point {
    const radians =
        (angleDegrees * Math.PI) /
        180

    return {
        x:
            center.x +
            Math.cos(radians) *
                radius,

        y:
            center.y +
            Math.sin(radians) *
                radius,
    }
}


function estimatedRadius(
    node: UniverseNode,
): number {
    switch (node.type) {
        case 'manufacturer':
            return 58

        case 'model':
            return 56

        case 'variant':
            return 38

        case 'version':
            return 44

        case 'engine_family':
            return 42
    }
}


function formatYears(
    start: number | null,
    end: number | null,
): string | null {
    if (
        start === null &&
        end === null
    ) {
        return null
    }

    if (
        start !== null &&
        end !== null
    ) {
        return `${start}–${end}`
    }

    if (start !== null) {
        return `${start}–`
    }

    return `–${end}`
}


function calculateLayout(
    graph: UniverseGraph,
): Map<string, Point> {
    const positions =
        new Map<string, Point>()

    const nodesById =
        new Map(
            graph.nodes.map(
                (node) => [
                    node.id,
                    node,
                ],
            ),
        )

    const manufacturers =
        graph.nodes
            .filter(
                (node) =>
                    node.type ===
                    'manufacturer',
            )
            .sort(
                (a, b) =>
                    a.label.localeCompare(
                        b.label,
                    ),
            )

    const metrics =
        manufacturers.map(
            (manufacturer) => {
                const models =
                    graph.nodes.filter(
                        (node) =>
                            node.type ===
                                'model' &&
                            node.manufacturer_id ===
                                manufacturer.id,
                    )

                const variants =
                    graph.nodes.filter(
                        (node) =>
                            node.type ===
                                'variant' &&
                            node.manufacturer_id ===
                                manufacturer.id,
                    )

                const modelRadius =
                    Math.max(
                        190,

                        (models.length *
                            118) /
                            (2 *
                                Math.PI),
                    )

                const variantRadius =
                    Math.max(
                        modelRadius +
                            230,

                        (variants.length *
                            86) /
                            (2 *
                                Math.PI),
                    )

                return {
                    manufacturer,
                    models,
                    variants,
                    modelRadius,
                    variantRadius,
                    islandRadius:
                        variantRadius +
                        230,
                }
            },
        )

    const maxIslandRadius =
        Math.max(
            450,
            ...metrics.map(
                (metric) =>
                    metric.islandRadius,
            ),
        )

    const columns =
        Math.max(
            1,
            Math.ceil(
                Math.sqrt(
                    metrics.length,
                ),
            ),
        )

    const spacing =
        maxIslandRadius * 2 +
        500

    const centers =
        metrics.map(
            (_, index) => ({
                x:
                    (index %
                        columns) *
                    spacing,

                y:
                    Math.floor(
                        index /
                            columns,
                    ) * spacing,
            }),
        )

    if (
        centers.length > 0
    ) {
        const centerX =
            centers.reduce(
                (sum, point) =>
                    sum + point.x,
                0,
            ) /
            centers.length

        const centerY =
            centers.reduce(
                (sum, point) =>
                    sum + point.y,
                0,
            ) /
            centers.length

        for (const center of
            centers) {
            center.x -= centerX
            center.y -= centerY
        }
    }

    const islandRadiusByManufacturer =
        new Map<
            string,
            number
        >()

    metrics.forEach(
        (
            metric,
            manufacturerIndex,
        ) => {
            const center =
                centers[
                    manufacturerIndex
                ]

            const {
                manufacturer,
                models,
                variants,
                modelRadius,
                variantRadius,
                islandRadius,
            } = metric

            positions.set(
                manufacturer.id,
                center,
            )

            islandRadiusByManufacturer.set(
                manufacturer.id,
                islandRadius,
            )

            const directVariants =
                variants.filter(
                    (variant) =>
                        variant.parent_model_id ===
                        null,
                )

            const branches = [
                ...models.map(
                    (model) => ({
                        kind:
                            'model' as const,

                        node: model,

                        variants:
                            variants.filter(
                                (
                                    variant,
                                ) =>
                                    variant.parent_model_id ===
                                    model.id,
                            ),
                    }),
                ),

                ...directVariants.map(
                    (variant) => ({
                        kind:
                            'direct-variant' as const,

                        node: variant,

                        variants: [
                            variant,
                        ],
                    }),
                ),
            ]

            const totalWeight =
                Math.max(
                    1,
                    branches.reduce(
                        (
                            sum,
                            branch,
                        ) =>
                            sum +
                            Math.max(
                                1,
                                branch
                                    .variants
                                    .length,
                            ),
                        0,
                    ),
                )

            let cursor = -90

            for (const branch of
                branches) {
                const weight =
                    Math.max(
                        1,
                        branch.variants
                            .length,
                    )

                const span =
                    (weight /
                        totalWeight) *
                    360

                const centerAngle =
                    cursor +
                    span / 2

                if (
                    branch.kind ===
                    'model'
                ) {
                    positions.set(
                        branch.node.id,
                        polar(
                            center,
                            modelRadius,
                            centerAngle,
                        ),
                    )
                }

                if (
                    branch.kind ===
                    'direct-variant'
                ) {
                    positions.set(
                        branch.node.id,
                        polar(
                            center,
                            variantRadius,
                            centerAngle,
                        ),
                    )

                    cursor += span

                    continue
                }

                const count =
                    branch.variants
                        .length

                const padding =
                    Math.min(
                        12,
                        span * 0.14,
                    )

                const usableSpan =
                    Math.max(
                        0,
                        span -
                            padding * 2,
                    )

                branch.variants
                    .sort(
                        (a, b) =>
                            a.label.localeCompare(
                                b.label,
                            ),
                    )
                    .forEach(
                        (
                            variant,
                            index,
                        ) => {
                            let angle =
                                centerAngle

                            if (
                                count > 1
                            ) {
                                angle =
                                    cursor +
                                    padding +
                                    (usableSpan *
                                        index) /
                                        (count -
                                            1)
                            }

                            positions.set(
                                variant.id,
                                polar(
                                    center,
                                    variantRadius,
                                    angle,
                                ),
                            )
                        },
                    )

                cursor += span
            }
        },
    )

    const versionsByVariant =
        new Map<
            string,
            UniverseNode[]
        >()

    for (const node of
        graph.nodes) {
        if (
            node.type !==
                'version' ||
            node.parent_variant_id ===
                null
        ) {
            continue
        }

        const versions =
            versionsByVariant.get(
                node.parent_variant_id,
            ) ?? []

        versions.push(node)

        versionsByVariant.set(
            node.parent_variant_id,
            versions,
        )
    }

    for (const [
        variantId,
        versions,
    ] of versionsByVariant) {
        const variant =
            nodesById.get(
                variantId,
            )

        const variantPosition =
            positions.get(
                variantId,
            )

        if (
            variant ===
                undefined ||
            variantPosition ===
                undefined ||
            variant.manufacturer_id ===
                null
        ) {
            continue
        }

        const manufacturerPosition =
            positions.get(
                variant.manufacturer_id,
            )

        if (
            manufacturerPosition ===
            undefined
        ) {
            continue
        }

        const dx =
            variantPosition.x -
            manufacturerPosition.x

        const dy =
            variantPosition.y -
            manufacturerPosition.y

        const length =
            Math.sqrt(
                dx * dx + dy * dy,
            ) || 1

        const directionX =
            dx / length

        const directionY =
            dy / length

        const perpendicularX =
            -directionY

        const perpendicularY =
            directionX

        /*
         * Versions live in a narrow radial "lane" behind their Variant.
         *
         * The old layout placed every Version at the same radial distance
         * and spread them sideways. That looks great when only one Variant
         * exists, but in a dense manufacturer island the fan crosses the
         * neighbouring Variant lanes.
         *
         * Here every Version moves progressively farther away from the
         * manufacturer in the same direction as its parent Variant. A tiny
         * alternating wobble keeps the edges from sitting perfectly on top
         * of each other without letting the Versions spill into neighbouring
         * Variant lanes.
         */
        versions
            .sort(
                (a, b) =>
                    a.label.localeCompare(
                        b.label,
                    ),
            )
            .forEach(
                (
                    version,
                    index,
                ) => {
                    const radialDistance =
                        VERSION_DISTANCE +
                        index *
                            VERSION_RADIAL_GAP

                    let sideOffset = 0

                    if (index > 0) {
                        sideOffset =
                            (index % 2 ===
                            0
                                ? -1
                                : 1) *
                            VERSION_LANE_WOBBLE
                    }

                    positions.set(
                        version.id,
                        {
                            x:
                                variantPosition.x +
                                directionX *
                                    radialDistance +
                                perpendicularX *
                                    sideOffset,

                            y:
                                variantPosition.y +
                                directionY *
                                    radialDistance +
                                perpendicularY *
                                    sideOffset,
                        },
                    )
                },
            )
    }

    const engineEdges =
        graph.edges.filter(
            (edge) =>
                edge.type ===
                'engine',
        )

    const engineNodes =
        graph.nodes
            .filter(
                (node) =>
                    node.type ===
                    'engine_family',
            )
            .sort(
                (a, b) =>
                    a.label.localeCompare(
                        b.label,
                    ),
            )

    engineNodes.forEach(
        (
            engineNode,
            engineIndex,
        ) => {
            const connectedVersionIds =
                engineEdges
                    .filter(
                        (edge) =>
                            edge.target ===
                            engineNode.id,
                    )
                    .map(
                        (edge) =>
                            edge.source,
                    )

            const connectedVersions =
                connectedVersionIds
                    .map(
                        (versionId) =>
                            nodesById.get(
                                versionId,
                            ),
                    )
                    .filter(
                        (
                            node,
                        ): node is UniverseNode =>
                            node !==
                            undefined,
                    )

            const manufacturerIds =
                [
                    ...new Set(
                        connectedVersions
                            .map(
                                (
                                    version,
                                ) =>
                                    version.manufacturer_id,
                            )
                            .filter(
                                (
                                    id,
                                ): id is string =>
                                    id !==
                                    null,
                            ),
                    ),
                ]

            if (
                manufacturerIds.length >
                1
            ) {
                const manufacturerCenters =
                    manufacturerIds
                        .map(
                            (
                                manufacturerId,
                            ) =>
                                positions.get(
                                    manufacturerId,
                                ),
                        )
                        .filter(
                            (
                                point,
                            ): point is Point =>
                                point !==
                                undefined,
                        )

                if (
                    manufacturerCenters.length >
                    0
                ) {
                    const averageX =
                        manufacturerCenters.reduce(
                            (
                                sum,
                                point,
                            ) =>
                                sum +
                                point.x,
                            0,
                        ) /
                        manufacturerCenters.length

                    const averageY =
                        manufacturerCenters.reduce(
                            (
                                sum,
                                point,
                            ) =>
                                sum +
                                point.y,
                            0,
                        ) /
                        manufacturerCenters.length

                    const offset =
                        (engineIndex %
                            2 ===
                        0
                            ? -1
                            : 1) *
                        (110 +
                            Math.floor(
                                engineIndex /
                                    2,
                            ) *
                                30)

                    positions.set(
                        engineNode.id,
                        {
                            x: averageX,
                            y:
                                averageY +
                                offset,
                        },
                    )

                    return
                }
            }

            const manufacturerId =
                manufacturerIds[0]

            if (
                manufacturerId ===
                undefined
            ) {
                return
            }

            const manufacturerPosition =
                positions.get(
                    manufacturerId,
                )

            if (
                manufacturerPosition ===
                undefined
            ) {
                return
            }

            const connectedPositions =
                connectedVersionIds
                    .map(
                        (versionId) =>
                            positions.get(
                                versionId,
                            ),
                    )
                    .filter(
                        (
                            point,
                        ): point is Point =>
                            point !==
                            undefined,
                    )

            if (
                connectedPositions.length ===
                0
            ) {
                return
            }

            const averageX =
                connectedPositions.reduce(
                    (
                        sum,
                        point,
                    ) =>
                        sum +
                        point.x,
                    0,
                ) /
                connectedPositions.length

            const averageY =
                connectedPositions.reduce(
                    (
                        sum,
                        point,
                    ) =>
                        sum +
                        point.y,
                    0,
                ) /
                connectedPositions.length

            const dx =
                averageX -
                manufacturerPosition.x

            const dy =
                averageY -
                manufacturerPosition.y

            const length =
                Math.sqrt(
                    dx * dx + dy * dy,
                ) || 1

            const islandRadius =
                islandRadiusByManufacturer.get(
                    manufacturerId,
                ) ?? 600

            positions.set(
                engineNode.id,
                {
                    x:
                        manufacturerPosition.x +
                        (dx / length) *
                            (islandRadius +
                                80),

                    y:
                        manufacturerPosition.y +
                        (dy / length) *
                            (islandRadius +
                                80),
                },
            )
        },
    )

    /*
     * Small collision pass. Manufacturer anchors stay fixed.
     */
    for (
        let iteration = 0;
        iteration < 6;
        iteration += 1
    ) {
        for (
            let leftIndex = 0;
            leftIndex <
            graph.nodes.length;
            leftIndex += 1
        ) {
            const leftNode =
                graph.nodes[
                    leftIndex
                ]

            const left =
                positions.get(
                    leftNode.id,
                )

            if (
                left === undefined
            ) {
                continue
            }

            for (
                let rightIndex =
                    leftIndex + 1;
                rightIndex <
                graph.nodes.length;
                rightIndex += 1
            ) {
                const rightNode =
                    graph.nodes[
                        rightIndex
                    ]

                const right =
                    positions.get(
                        rightNode.id,
                    )

                if (
                    right ===
                    undefined
                ) {
                    continue
                }

                const dx =
                    right.x -
                    left.x

                const dy =
                    right.y -
                    left.y

                const distance =
                    Math.sqrt(
                        dx * dx +
                            dy * dy,
                    ) || 0.001

                const minimum =
                    estimatedRadius(
                        leftNode,
                    ) +
                    estimatedRadius(
                        rightNode,
                    ) +
                    NODE_GAP

                if (
                    distance >=
                    minimum
                ) {
                    continue
                }

                const overlap =
                    minimum -
                    distance

                const nx =
                    dx / distance

                const ny =
                    dy / distance

                const leftMovable =
                    leftNode.type !==
                    'manufacturer'

                const rightMovable =
                    rightNode.type !==
                    'manufacturer'

                if (
                    leftMovable &&
                    rightMovable
                ) {
                    left.x -=
                        nx *
                        overlap *
                        0.5

                    left.y -=
                        ny *
                        overlap *
                        0.5

                    right.x +=
                        nx *
                        overlap *
                        0.5

                    right.y +=
                        ny *
                        overlap *
                        0.5
                } else if (
                    rightMovable
                ) {
                    right.x +=
                        nx * overlap

                    right.y +=
                        ny * overlap
                } else if (
                    leftMovable
                ) {
                    left.x -=
                        nx * overlap

                    left.y -=
                        ny * overlap
                }
            }
        }
    }

    return positions
}


function buildElements(
    graph: UniverseGraph,
    positions: Map<string, Point>,
): ElementDefinition[] {
    const nodeElements =
        graph.nodes.map(
            (
                node,
            ): ElementDefinition => ({
                data: {
                    ...node,
                },

                position: (() => {
                    const point =
                        positions.get(
                            node.id,
                        )

                    return point ===
                        undefined
                        ? {
                              x: 0,
                              y: 0,
                          }
                        : {
                              x: point.x,
                              y: point.y,
                          }
                })(),
            }),
        )

    const edgeElements =
        graph.edges.map(
            (
                edge,
            ): ElementDefinition => ({
                data: {
                    ...edge,
                },
            }),
        )

    return [
        ...nodeElements,
        ...edgeElements,
    ]
}


function buildShortestRoutes(
    graph: UniverseGraph,
    startId: string,
    endId: string,
): ShortestRoute[] {
    if (startId === endId) {
        return []
    }

    const adjacency =
        new Map<
            string,
            {
                nodeId: string
                edgeId: string
            }[]
        >()

    for (const node of
        graph.nodes) {
        adjacency.set(
            node.id,
            [],
        )
    }

    for (const edge of
        graph.edges) {
        adjacency
            .get(edge.source)
            ?.push({
                nodeId:
                    edge.target,

                edgeId:
                    edge.id,
            })

        adjacency
            .get(edge.target)
            ?.push({
                nodeId:
                    edge.source,

                edgeId:
                    edge.id,
            })
    }

    const distances =
        new Map<
            string,
            number
        >()

    const predecessors =
        new Map<
            string,
            {
                nodeId: string
                edgeId: string
            }[]
        >()

    const queue: string[] = [
        startId,
    ]

    distances.set(
        startId,
        0,
    )

    let targetDistance:
        | number
        | null = null

    for (
        let index = 0;
        index < queue.length;
        index += 1
    ) {
        const current =
            queue[index]

        const currentDistance =
            distances.get(
                current,
            ) ?? 0

        if (
            targetDistance !==
                null &&
            currentDistance >=
                targetDistance
        ) {
            continue
        }

        for (const step of
            adjacency.get(
                current,
            ) ?? []) {
            const nextDistance =
                currentDistance + 1

            const knownDistance =
                distances.get(
                    step.nodeId,
                )

            if (
                knownDistance ===
                undefined
            ) {
                distances.set(
                    step.nodeId,
                    nextDistance,
                )

                predecessors.set(
                    step.nodeId,
                    [
                        {
                            nodeId:
                                current,

                            edgeId:
                                step.edgeId,
                        },
                    ],
                )

                queue.push(
                    step.nodeId,
                )

                if (
                    step.nodeId ===
                    endId
                ) {
                    targetDistance =
                        nextDistance
                }

                continue
            }

            if (
                knownDistance ===
                nextDistance
            ) {
                const previous =
                    predecessors.get(
                        step.nodeId,
                    ) ?? []

                previous.push({
                    nodeId:
                        current,

                    edgeId:
                        step.edgeId,
                })

                predecessors.set(
                    step.nodeId,
                    previous,
                )
            }
        }
    }

    if (
        !distances.has(
            endId,
        )
    ) {
        return []
    }

    const routes:
        ShortestRoute[] = []

    function reconstruct(
        currentId: string,
        reverseNodes: string[],
        reverseEdges: string[],
    ) {
        if (
            routes.length >=
            MAX_SHORTEST_ROUTES
        ) {
            return
        }

        if (
            currentId ===
            startId
        ) {
            routes.push({
                nodeIds: [
                    ...reverseNodes,
                    startId,
                ].reverse(),

                edgeIds: [
                    ...reverseEdges,
                ].reverse(),
            })

            return
        }

        for (const predecessor of
            predecessors.get(
                currentId,
            ) ?? []) {
            reconstruct(
                predecessor.nodeId,

                [
                    ...reverseNodes,
                    currentId,
                ],

                [
                    ...reverseEdges,
                    predecessor.edgeId,
                ],
            )
        }
    }

    reconstruct(
        endId,
        [],
        [],
    )

    return routes
}


function buildNodeInfo(
    node: UniverseNode,
    nodesById: Map<
        string,
        UniverseNode
    >,
    versionCountByVariant: Map<
        string,
        number
    >,
): NodeInfo {
    const manufacturer =
        node.manufacturer_id ===
        null
            ? null
            : nodesById.get(
                  node.manufacturer_id,
              )

    const model =
        node.parent_model_id ===
        null
            ? null
            : nodesById.get(
                  node.parent_model_id,
              )

    const variant =
        node.parent_variant_id ===
        null
            ? null
            : nodesById.get(
                  node.parent_variant_id,
              )

    if (
        node.type ===
        'manufacturer'
    ) {
        const modelCount = [
            ...nodesById.values(),
        ].filter(
            (candidate) =>
                candidate.type ===
                    'model' &&
                candidate.manufacturer_id ===
                    node.id,
        ).length

        const variantCount = [
            ...nodesById.values(),
        ].filter(
            (candidate) =>
                candidate.type ===
                    'variant' &&
                candidate.manufacturer_id ===
                    node.id,
        ).length

        return {
            type:
                'Manufacturer',

            title:
                node.label,

            rows: [
                {
                    label:
                        'Discovered models',

                    value:
                        String(
                            modelCount,
                        ),
                },

                {
                    label:
                        'Discovered variants',

                    value:
                        String(
                            variantCount,
                        ),
                },
            ],
        }
    }

    if (
        node.type === 'model'
    ) {
        const variantCount = [
            ...nodesById.values(),
        ].filter(
            (candidate) =>
                candidate.type ===
                    'variant' &&
                candidate.parent_model_id ===
                    node.id,
        ).length

        return {
            type: 'Model',

            title:
                node.label,

            subtitle:
                manufacturer?.label,

            rows: [
                {
                    label:
                        'Discovered variants',

                    value:
                        String(
                            variantCount,
                        ),
                },
            ],
        }
    }

    if (
        node.type ===
        'variant'
    ) {
        const rows:
            InfoRow[] = []

        const years =
            formatYears(
                node.production_start,
                node.production_end,
            )

        if (
            years !== null
        ) {
            rows.push({
                label:
                    'Production',

                value:
                    years,
            })
        }

        if (
            node.vehicle_classes
                .length > 0
        ) {
            rows.push({
                label:
                    'Class',

                value:
                    node.vehicle_classes.join(
                        ', ',
                    ),
            })
        }

        if (
            node.body_styles.length >
            0
        ) {
            rows.push({
                label:
                    'Body styles',

                value:
                    node.body_styles.join(
                        ', ',
                    ),
            })
        }

        if (
            node.drivetrains.length >
            0
        ) {
            rows.push({
                label:
                    'Drivetrain',

                value:
                    node.drivetrains.join(
                        ', ',
                    ),
            })
        }

        rows.push({
            label:
                'Discovered versions',

            value:
                String(
                    versionCountByVariant.get(
                        node.id,
                    ) ?? 0,
                ),
        })

        return {
            type:
                'Variant',

            title:
                node.label,

            subtitle: [
                manufacturer?.label,
                model?.label,
            ]
                .filter(Boolean)
                .join(' · '),

            rows,
        }
    }

    if (
        node.type ===
        'version'
    ) {
        const rows:
            InfoRow[] = []

        if (
            node.power_hp !==
            null
        ) {
            rows.push({
                label:
                    'Power',

                value:
                    `${node.power_hp} hp`,
            })
        }

        if (
            node.engine_labels
                .length > 0
        ) {
            rows.push({
                label:
                    'Engine',

                value:
                    node.engine_labels.join(
                        ', ',
                    ),
            })
        }

        return {
            type:
                'Version',

            title:
                node.label,

            subtitle: [
                manufacturer?.label,
                model?.label,
                variant?.label,
            ]
                .filter(Boolean)
                .join(' · '),

            rows,
        }
    }

    return {
        type:
            'Engine family',

        title:
            node.label,

        rows: [],
    }
}


function AutomotiveUniverse({
    unlockedVehicleIds,
    newlyUnlockedVehicleId,
    onUnlockAnimationComplete,
}: AutomotiveUniverseProps) {
    const graphRef =
        useRef<HTMLDivElement>(
            null,
        )

    const cyRef =
        useRef<Core | null>(
            null,
        )

    const actionsRef =
        useRef<
            GraphActions | null
        >(null)

    const expandedVariantsRef =
        useRef<Set<string>>(
            new Set(),
        )

    const routeModeRef =
        useRef(false)

    const routeStartRef =
        useRef<string | null>(
            null,
        )

    const canvasMovedRef =
        useRef(false)

    const centeredNodeIdsRef =
        useRef<Set<string>>(
            new Set(),
        )

    const onUnlockAnimationCompleteRef =
        useRef(
            onUnlockAnimationComplete,
        )

    useEffect(() => {
        onUnlockAnimationCompleteRef.current =
            onUnlockAnimationComplete
    }, [onUnlockAnimationComplete])

    const [graph, setGraph] =
        useState<
            UniverseGraph | null
        >(null)

    const [
        isLoading,
        setIsLoading,
    ] = useState(true)

    const [error, setError] =
        useState<string | null>(
            null,
        )

    const [status, setStatus] =
        useState(
            'Base universe — click a node',
        )

    const [
        controlsOpen,
        setControlsOpen,
    ] = useState(false)

    const [
        routeMode,
        setRouteMode,
    ] = useState(false)

    const [
        selectedNodeId,
        setSelectedNodeId,
    ] =
        useState<string | null>(
            null,
        )

    const [
        routeResult,
        setRouteResult,
    ] = useState<{
        startId: string
        endId: string
        routes: ShortestRoute[]
    } | null>(null)

    const nodesById =
        useMemo(
            () =>
                new Map(
                    graph?.nodes.map(
                        (node) => [
                            node.id,
                            node,
                        ],
                    ) ?? [],
                ),
            [graph],
        )

    const versionCountByVariant =
        useMemo(() => {
            const counts =
                new Map<
                    string,
                    number
                >()

            for (const node of
                graph?.nodes ?? []) {
                if (
                    node.type !==
                        'version' ||
                    node.parent_variant_id ===
                        null
                ) {
                    continue
                }

                counts.set(
                    node.parent_variant_id,

                    (counts.get(
                        node.parent_variant_id,
                    ) ?? 0) + 1,
                )
            }

            return counts
        }, [graph])

    const selectedInfo =
        selectedNodeId ===
        null
            ? null
            : (() => {
                  const node =
                      nodesById.get(
                          selectedNodeId,
                      )

                  if (
                      node ===
                      undefined
                  ) {
                      return null
                  }

                  return buildNodeInfo(
                      node,
                      nodesById,
                      versionCountByVariant,
                  )
              })()

    useEffect(() => {
        const controller =
            new AbortController()

        async function loadGraph() {
            try {
                setIsLoading(true)
                setError(null)

                const response =
                    await fetch(
                        '/api/universe/graph',
                        {
                            method:
                                'POST',

                            headers: {
                                'Content-Type':
                                    'application/json',
                            },

                            body: JSON.stringify(
                                {
                                    unlocked_vehicle_ids:
                                        unlockedVehicleIds,
                                },
                            ),

                            signal:
                                controller.signal,
                        },
                    )

                if (
                    !response.ok
                ) {
                    throw new Error(
                        'Universe request failed.',
                    )
                }

                const data =
                    (await response.json()) as UniverseGraph

                setGraph(data)
            } catch (
                loadError
            ) {
                if (
                    loadError instanceof
                        Error &&
                    loadError.name ===
                        'AbortError'
                ) {
                    return
                }

                console.error(
                    loadError,
                )

                setError(
                    'Could not load the Automotive Universe.',
                )
            } finally {
                if (
                    !controller.signal
                        .aborted
                ) {
                    setIsLoading(
                        false,
                    )
                }
            }
        }

        loadGraph()

        return () => {
            controller.abort()
        }
    }, [
        unlockedVehicleIds,
    ])

    useEffect(() => {
        if (
            graph === null ||
            graphRef.current ===
                null
        ) {
            return
        }

        const positions =
            calculateLayout(graph)

        const cy =
            cytoscape({
                container:
                    graphRef.current,

                elements:
                    buildElements(
                        graph,
                        positions,
                    ),

                autoungrabify:
                    true,

                style: [
                    {
                        selector:
                            'node',

                        style: {
                            label:
                                'data(label)',

                            'font-family':
                                'Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif',

                            'font-size':
                                12,

                            'font-weight':
                                600,

                            'text-valign':
                                'center',

                            'text-halign':
                                'center',

                            'transition-property':
                                'opacity, border-width, border-color, background-color',

                            'transition-duration':
                                180,
                        },
                    },

                    {
                        selector:
                            'node[type = "manufacturer"]',

                        style: {
                            width: 104,
                            height: 104,

                            shape:
                                'ellipse',

                            'background-color':
                                '#e7e9ed',

                            color:
                                '#111318',

                            'font-size':
                                17,

                            'font-weight':
                                700,

                            'border-width':
                                3,

                            'border-color':
                                '#ffffff',



                        },
                    },

                    {
                        selector:
                            'node[type = "model"]',

                        style: {
                            width: 94,
                            height: 48,

                            shape:
                                'round-rectangle',

                            'background-color':
                                '#334f6b',

                            color:
                                '#edf2f7',

                            'border-width':
                                1.5,

                            'border-color':
                                '#527394',
                        },
                    },

                    {
                        selector:
                            'node[type = "variant"]',

                        style: {
                            width: 66,
                            height: 66,

                            shape:
                                'ellipse',

                            'background-color':
                                '#4f756b',

                            color:
                                '#f0f5f3',

                            'border-width':
                                2,

                            'border-color':
                                '#74998f',



                        },
                    },

                    {
                        selector:
                            'node[type = "version"]',

                        style: {
                            width: 72,
                            height: 38,

                            shape:
                                'round-rectangle',

                            'background-color':
                                '#a78b55',

                            color:
                                '#f7f1e5',

                            'border-width':
                                1,

                            'border-color':
                                '#c3aa77',

                            'font-size':
                                11,
                        },
                    },

                    {
                        selector:
                            'node[type = "engine_family"]',

                        style: {
                            width: 64,
                            height: 64,

                            shape:
                                'diamond',

                            'background-color':
                                '#665a7c',

                            color:
                                '#f1edf7',

                            'border-width':
                                1.5,

                            'border-color':
                                '#8e7fa5',

                            'font-weight':
                                700,

                            'font-size':
                                11,



                        },
                    },

                    {
                        selector:
                            'edge[type = "hierarchy"]',

                        style: {
                            width: 2,

                            'line-color':
                                '#343a45',

                            'curve-style':
                                'straight',

                            opacity:
                                0.9,
                        },
                    },

                    {
                        selector:
                            'edge[type = "version"]',

                        style: {
                            width:
                                1.8,

                            'line-color':
                                '#756746',

                            'curve-style':
                                'straight',

                            opacity:
                                0.75,
                        },
                    },

                    {
                        selector:
                            'edge[type = "engine"]',

                        style: {
                            width: 2,

                            'line-color':
                                '#665a78',

                            'line-style':
                                'dashed',

                            'curve-style':
                                'bezier',

                            opacity:
                                0.75,
                        },
                    },

                    {
                        selector:
                            '.dimmed',

                        style: {
                            opacity:
                                0.055,
                        },
                    },

                    {
                        selector:
                            '.focused',

                        style: {
                            opacity: 1,
                        },
                    },

                    {
                        selector:
                            '.newly-unlocked',

                        style: {
                            'border-color':
                                '#e5c268',

                            'underlay-color':
                                '#e5c268',

                            'underlay-opacity':
                                0.22,

                            'underlay-padding':
                                18,



                        },
                    },

                    {
                        selector:
                            '.route-start',

                        style: {
                            'border-width':
                                5,

                            'border-color':
                                '#7ea4c7',

                            'underlay-color':
                                '#5f82a4',

                            'underlay-opacity':
                                0.2,

                            'underlay-padding':
                                12,
                        },
                    },

                    {
                        selector:
                            '.route-end',

                        style: {
                            'border-width':
                                5,

                            'border-color':
                                '#d8b96f',

                            'underlay-color':
                                '#b99b5e',

                            'underlay-opacity':
                                0.2,

                            'underlay-padding':
                                12,
                        },
                    },

                    {
                        selector:
                            'edge.route-path',

                        style: {
                            width:
                                3.2,

                            opacity:
                                1,
                        },
                    },
                ],

                layout: {
                    name:
                        'preset',

                    fit: false,
                },
            })

        cyRef.current = cy

        const detailAnimationTimeouts:
            number[] = []

        const unlockAnimationTimeouts:
            number[] = []

        function scheduleAnimation(
            callback: () => void,
            delay: number,
        ) {
            if (delay <= 0) {
                callback()
                return
            }

            detailAnimationTimeouts.push(
                window.setTimeout(
                    callback,
                    delay,
                ),
            )
        }

        function scheduleUnlockAnimation(
            callback: () => void,
            delay: number,
        ) {
            if (delay <= 0) {
                callback()
                return
            }

            unlockAnimationTimeouts.push(
                window.setTimeout(
                    callback,
                    delay,
                ),
            )
        }

        function clearDetailAnimationTimeouts() {
            while (
                detailAnimationTimeouts.length >
                0
            ) {
                const timeoutId =
                    detailAnimationTimeouts.pop()

                if (
                    timeoutId !==
                    undefined
                ) {
                    window.clearTimeout(
                        timeoutId,
                    )
                }
            }
        }

        function clearUnlockAnimationTimeouts() {
            while (
                unlockAnimationTimeouts.length >
                0
            ) {
                const timeoutId =
                    unlockAnimationTimeouts.pop()

                if (
                    timeoutId !==
                    undefined
                ) {
                    window.clearTimeout(
                        timeoutId,
                    )
                }
            }
        }

        const positionAnimationFrames =
            new Map<string, number>()

        function cancelPositionAnimation(
            nodeId: string,
        ) {
            const frame =
                positionAnimationFrames.get(
                    nodeId,
                )

            if (frame !== undefined) {
                window.cancelAnimationFrame(
                    frame,
                )

                positionAnimationFrames.delete(
                    nodeId,
                )
            }
        }

        function clearPositionAnimations() {
            for (const frame of
                positionAnimationFrames.values()) {
                window.cancelAnimationFrame(
                    frame,
                )
            }

            positionAnimationFrames.clear()
        }

        function animateNodePosition(
            node: NodeSingular,
            from: Point,
            to: Point,
            duration: number,
            complete?: () => void,
        ) {
            cancelPositionAnimation(
                node.id(),
            )

            if (
                duration <= 0 ||
                prefersReducedMotion()
            ) {
                node.position(to)
                complete?.()
                return
            }

            node.position(from)

            const startedAt =
                performance.now()

            const tick = (
                now: number,
            ) => {
                const rawProgress =
                    Math.min(
                        1,
                        Math.max(
                            0,
                            (now - startedAt) /
                                duration,
                        ),
                    )

                /*
                 * Ease-out cubic. This gives the same soft "fan out"
                 * feeling as the prototype while guaranteeing that
                 * every node ends exactly at its calculated position.
                 */
                const progress =
                    1 -
                    Math.pow(
                        1 - rawProgress,
                        3,
                    )

                node.position({
                    x:
                        from.x +
                        (to.x - from.x) *
                            progress,

                    y:
                        from.y +
                        (to.y - from.y) *
                            progress,
                })

                if (rawProgress < 1) {
                    const frame =
                        window.requestAnimationFrame(
                            tick,
                        )

                    positionAnimationFrames.set(
                        node.id(),
                        frame,
                    )

                    return
                }

                node.position(to)

                positionAnimationFrames.delete(
                    node.id(),
                )

                complete?.()
            }

            const frame =
                window.requestAnimationFrame(
                    tick,
                )

            positionAnimationFrames.set(
                node.id(),
                frame,
            )
        }

        function finalPosition(
            nodeId: string,
        ): Point | null {
            const point =
                positions.get(
                    nodeId,
                )

            if (point === undefined) {
                return null
            }

            /*
             * Important: return a copy.
             *
             * Cytoscape may keep/mutate position objects. If we hand
             * the layout map's object back directly, moving a Version
             * to its Variant for the start of the animation can also
             * mutate the saved "final" position. The animation then
             * becomes origin -> origin and every Version stacks up.
             */
            return {
                x: point.x,
                y: point.y,
            }
        }


        function clonePoint(
            point: Point,
        ): Point {
            return {
                x: point.x,
                y: point.y,
            }
        }

        function averageAngles(
            angles: number[],
        ): number {
            if (angles.length === 0) {
                return -90
            }

            const x =
                angles.reduce(
                    (
                        sum,
                        angle,
                    ) =>
                        sum +
                        Math.cos(
                            (angle *
                                Math.PI) /
                                180,
                        ),
                    0,
                )

            const y =
                angles.reduce(
                    (
                        sum,
                        angle,
                    ) =>
                        sum +
                        Math.sin(
                            (angle *
                                Math.PI) /
                                180,
                        ),
                    0,
                )

            return (
                Math.atan2(
                    y,
                    x,
                ) *
                180 /
                Math.PI
            )
        }

        function ringRadius(
            nodeCount: number,
            minimum: number,
        ): number {
            if (nodeCount <= 1) {
                return minimum
            }

            const circumferenceNeeded =
                nodeCount *
                CENTER_MIN_NODE_ARC

            return Math.max(
                minimum,
                circumferenceNeeded /
                    (2 *
                        Math.PI),
            )
        }

        function restoreCenteredLayout() {
            if (
                centeredNodeIdsRef.current
                    .size === 0
            ) {
                return
            }

            clearPositionAnimations()

            for (const nodeId of
                centeredNodeIdsRef.current) {
                const node =
                    cy.$id(
                        nodeId,
                    )

                const base =
                    finalPosition(
                        nodeId,
                    )

                if (
                    node.empty() ||
                    base === null
                ) {
                    continue
                }

                ;(
                    node as unknown as NodeSingular
                ).position(
                    base,
                )
            }

            centeredNodeIdsRef.current.clear()
        }

        function centerEngineFamily(
            engineFamily:
                NodeSingular,
        ) {
            restoreCenteredLayout()
            clearClasses()
            resetAnimatedDetails()

            const engineId =
                engineFamily.id()

            const graphNodesById =
                new Map(
                    graph.nodes.map(
                        (node) => [
                            node.id,
                            node,
                        ],
                    ),
                )

            const connectedVersionIds =
                graph.edges
                    .filter(
                        (edge) =>
                            edge.type ===
                                'engine' &&
                            edge.target ===
                                engineId,
                    )
                    .map(
                        (edge) =>
                            edge.source,
                    )

            const connectedVersions =
                connectedVersionIds
                    .map(
                        (versionId) =>
                            graphNodesById.get(
                                versionId,
                            ),
                    )
                    .filter(
                        (
                            node,
                        ): node is UniverseNode =>
                            node !==
                                undefined &&
                            node.type ===
                                'version',
                    )

            if (
                connectedVersions.length ===
                0
            ) {
                cy.animate({
                    center: {
                        eles:
                            engineFamily,
                    },

                    duration:
                        300,
                })

                setStatus(
                    `${engineFamily.data('label')} centered`,
                )

                return
            }

            /*
             * Order the first ring hierarchically. Versions belonging
             * to the same Variant/Model stay next to one another, which
             * greatly reduces edge crossings in the later rings.
             */
            connectedVersions.sort(
                (
                    left,
                    right,
                ) => {
                    const leftVariant =
                        left.parent_variant_id ===
                        null
                            ? undefined
                            : graphNodesById.get(
                                  left.parent_variant_id,
                              )

                    const rightVariant =
                        right.parent_variant_id ===
                        null
                            ? undefined
                            : graphNodesById.get(
                                  right.parent_variant_id,
                              )

                    const leftModel =
                        left.parent_model_id ===
                        null
                            ? undefined
                            : graphNodesById.get(
                                  left.parent_model_id,
                              )

                    const rightModel =
                        right.parent_model_id ===
                        null
                            ? undefined
                            : graphNodesById.get(
                                  right.parent_model_id,
                              )

                    const leftManufacturer =
                        left.manufacturer_id ===
                        null
                            ? undefined
                            : graphNodesById.get(
                                  left.manufacturer_id,
                              )

                    const rightManufacturer =
                        right.manufacturer_id ===
                        null
                            ? undefined
                            : graphNodesById.get(
                                  right.manufacturer_id,
                              )

                    return [
                        leftManufacturer
                            ?.label ?? '',
                        leftModel?.label ??
                            '',
                        leftVariant?.label ??
                            '',
                        left.label,
                    ]
                        .join('\u0000')
                        .localeCompare(
                            [
                                rightManufacturer
                                    ?.label ?? '',
                                rightModel
                                    ?.label ?? '',
                                rightVariant
                                    ?.label ?? '',
                                right.label,
                            ].join(
                                '\u0000',
                            ),
                        )
                },
            )

            const variantIds =
                [
                    ...new Set(
                        connectedVersions
                            .map(
                                (
                                    version,
                                ) =>
                                    version.parent_variant_id,
                            )
                            .filter(
                                (
                                    id,
                                ): id is string =>
                                    id !==
                                    null,
                            ),
                    ),
                ]

            const modelIds =
                [
                    ...new Set(
                        variantIds
                            .map(
                                (
                                    variantId,
                                ) =>
                                    graphNodesById.get(
                                        variantId,
                                    )
                                        ?.parent_model_id,
                            )
                            .filter(
                                (
                                    id,
                                ): id is string =>
                                    id !==
                                    null,
                            ),
                    ),
                ]

            const manufacturerIds =
                [
                    ...new Set(
                        connectedVersions
                            .map(
                                (
                                    version,
                                ) =>
                                    version.manufacturer_id,
                            )
                            .filter(
                                (
                                    id,
                                ): id is string =>
                                    id !==
                                    null,
                            ),
                    ),
                ]

            const focusNodeIds =
                new Set<string>([
                    engineId,
                    ...connectedVersionIds,
                    ...variantIds,
                    ...modelIds,
                    ...manufacturerIds,
                ])

            const focusEdgeIds =
                new Set<string>()

            for (const edge of
                graph.edges) {
                const bothFocused =
                    focusNodeIds.has(
                        edge.source,
                    ) &&
                    focusNodeIds.has(
                        edge.target,
                    )

                if (!bothFocused) {
                    continue
                }

                if (
                    edge.type ===
                        'engine' &&
                    edge.target !==
                        engineId
                ) {
                    continue
                }

                focusEdgeIds.add(
                    edge.id,
                )
            }

            /*
             * Ensure the whole semantic chain is visible:
             *
             * Engine family
             *   -> Versions
             *      -> Variants
             *         -> Models
             *            -> Manufacturer
             */
            cy.nodes().addClass(
                'dimmed',
            )

            cy.edges().addClass(
                'dimmed',
            )

            cy.nodes()
                .filter(
                    (node) =>
                        node.data(
                            'type',
                        ) ===
                        'engine_family',
                )
                .style(
                    'display',
                    'none',
                )

            for (const nodeId of
                focusNodeIds) {
                const node =
                    cy.$id(
                        nodeId,
                    )

                node.style(
                    'display',
                    'element',
                )

                node
                    .removeClass(
                        'dimmed',
                    )
                    .addClass(
                        'focused',
                    )
            }

            for (const edgeId of
                focusEdgeIds) {
                const edge =
                    cy.$id(
                        edgeId,
                    )

                edge.style(
                    'display',
                    'element',
                )

                edge
                    .removeClass(
                        'dimmed',
                    )
                    .addClass(
                        'focused',
                    )
            }

            const enginePosition =
                engineFamily.position()

            const center: Point = {
                x:
                    enginePosition.x,
                y:
                    enginePosition.y,
            }

            const versionAngles =
                new Map<
                    string,
                    number
                >()

            const firstRadius =
                ringRadius(
                    connectedVersions.length,
                    230,
                )

            const versionCount =
                connectedVersions.length

            connectedVersions.forEach(
                (
                    version,
                    index,
                ) => {
                    const angle =
                        -90 +
                        (360 *
                            index) /
                            versionCount

                    versionAngles.set(
                        version.id,
                        angle,
                    )
                },
            )

            const variantAngles =
                new Map<
                    string,
                    number
                >()

            for (const variantId of
                variantIds) {
                const childAngles =
                    connectedVersions
                        .filter(
                            (
                                version,
                            ) =>
                                version.parent_variant_id ===
                                variantId,
                        )
                        .map(
                            (
                                version,
                            ) =>
                                versionAngles.get(
                                    version.id,
                                ),
                        )
                        .filter(
                            (
                                angle,
                            ): angle is number =>
                                angle !==
                                undefined,
                        )

                variantAngles.set(
                    variantId,
                    averageAngles(
                        childAngles,
                    ),
                )
            }

            const modelAngles =
                new Map<
                    string,
                    number
                >()

            for (const modelId of
                modelIds) {
                const childAngles =
                    variantIds
                        .filter(
                            (
                                variantId,
                            ) =>
                                graphNodesById.get(
                                    variantId,
                                )
                                    ?.parent_model_id ===
                                modelId,
                        )
                        .map(
                            (
                                variantId,
                            ) =>
                                variantAngles.get(
                                    variantId,
                                ),
                        )
                        .filter(
                            (
                                angle,
                            ): angle is number =>
                                angle !==
                                undefined,
                        )

                modelAngles.set(
                    modelId,
                    averageAngles(
                        childAngles,
                    ),
                )
            }

            const manufacturerAngles =
                new Map<
                    string,
                    number
                >()

            for (const manufacturerId of
                manufacturerIds) {
                const childAngles:
                    number[] = []

                for (const modelId of
                    modelIds) {
                    const model =
                        graphNodesById.get(
                            modelId,
                        )

                    if (
                        model
                            ?.manufacturer_id !==
                        manufacturerId
                    ) {
                        continue
                    }

                    const angle =
                        modelAngles.get(
                            modelId,
                        )

                    if (
                        angle !==
                        undefined
                    ) {
                        childAngles.push(
                            angle,
                        )
                    }
                }

                /*
                 * Variants represented directly beneath a Manufacturer
                 * ("No Model" in the DB) still participate in this ring.
                 */
                for (const variantId of
                    variantIds) {
                    const variant =
                        graphNodesById.get(
                            variantId,
                        )

                    if (
                        variant
                            ?.manufacturer_id !==
                            manufacturerId ||
                        variant.parent_model_id !==
                            null
                    ) {
                        continue
                    }

                    const angle =
                        variantAngles.get(
                            variantId,
                        )

                    if (
                        angle !==
                        undefined
                    ) {
                        childAngles.push(
                            angle,
                        )
                    }
                }

                manufacturerAngles.set(
                    manufacturerId,
                    averageAngles(
                        childAngles,
                    ),
                )
            }

            const secondRadius =
                Math.max(
                    firstRadius +
                        CENTER_RING_GAP,
                    ringRadius(
                        variantIds.length,
                        firstRadius +
                            CENTER_RING_GAP,
                    ),
                )

            const thirdRadius =
                Math.max(
                    secondRadius +
                        CENTER_RING_GAP,
                    ringRadius(
                        modelIds.length,
                        secondRadius +
                            CENTER_RING_GAP,
                    ),
                )

            const fourthRadius =
                thirdRadius +
                CENTER_RING_GAP +
                40

            const targetPositions =
                new Map<
                    string,
                    Point
                >()

            targetPositions.set(
                engineId,
                center,
            )

            for (const version of
                connectedVersions) {
                const angle =
                    versionAngles.get(
                        version.id,
                    )

                if (
                    angle ===
                    undefined
                ) {
                    continue
                }

                targetPositions.set(
                    version.id,
                    polar(
                        center,
                        firstRadius,
                        angle,
                    ),
                )
            }

            for (const variantId of
                variantIds) {
                const angle =
                    variantAngles.get(
                        variantId,
                    )

                if (
                    angle ===
                    undefined
                ) {
                    continue
                }

                targetPositions.set(
                    variantId,
                    polar(
                        center,
                        secondRadius,
                        angle,
                    ),
                )
            }

            for (const modelId of
                modelIds) {
                const angle =
                    modelAngles.get(
                        modelId,
                    )

                if (
                    angle ===
                    undefined
                ) {
                    continue
                }

                targetPositions.set(
                    modelId,
                    polar(
                        center,
                        thirdRadius,
                        angle,
                    ),
                )
            }

            for (const manufacturerId of
                manufacturerIds) {
                const angle =
                    manufacturerAngles.get(
                        manufacturerId,
                    )

                if (
                    angle ===
                    undefined
                ) {
                    continue
                }

                targetPositions.set(
                    manufacturerId,
                    polar(
                        center,
                        fourthRadius,
                        angle,
                    ),
                )
            }

            centeredNodeIdsRef.current =
                new Set(
                    targetPositions.keys(),
                )

            for (const [
                nodeId,
                target,
            ] of targetPositions) {
                const node =
                    cy.$id(
                        nodeId,
                    )

                if (
                    node.empty()
                ) {
                    continue
                }

                const nodeSingular =
                    node as unknown as NodeSingular

                const current =
                    nodeSingular.position()

                animateNodePosition(
                    nodeSingular,
                    {
                        x:
                            current.x,
                        y:
                            current.y,
                    },
                    clonePoint(
                        target,
                    ),
                    CENTER_LAYOUT_DURATION,
                )
            }

            engineFamily.addClass(
                'route-start',
            )

            scheduleAnimation(
                () => {
                    const focused =
                        cy.elements().filter(
                            (
                                element,
                            ) =>
                                focusNodeIds.has(
                                    element.id(),
                                ) ||
                                focusEdgeIds.has(
                                    element.id(),
                                ),
                        )

                    cy.animate({
                        fit: {
                            eles:
                                focused,
                            padding:
                                100,
                        },

                        duration:
                            350,
                    })
                },
                CENTER_LAYOUT_DURATION +
                    40,
            )

            setStatus(
                `${engineFamily.data('label')} centered — versions → variants → models → manufacturer`,
            )
        }

        function resetAnimatedDetails() {
            clearDetailAnimationTimeouts()
            clearPositionAnimations()

            cy.nodes()
                .filter(
                    (node) =>
                        node.data(
                            'type',
                        ) ===
                            'version' ||
                        node.data(
                            'type',
                        ) ===
                            'engine_family',
                )
                .forEach(
                    (node) => {
                        node.stop()

                        const final =
                            finalPosition(
                                node.id(),
                            )

                        if (
                            final !==
                            null
                        ) {
                            node.position(
                                final,
                            )
                        }

                        node.removeStyle(
                            'opacity',
                        )
                    },
                )

            cy.edges()
                .filter(
                    (edge) =>
                        edge.data(
                            'type',
                        ) ===
                            'version' ||
                        edge.data(
                            'type',
                        ) ===
                            'engine',
                )
                .forEach(
                    (edge) => {
                        edge.stop()

                        edge.removeStyle(
                            'opacity',
                        )
                    },
                )
        }

        function clearClasses() {
            cy.elements().removeClass(
                'dimmed focused route-start route-end route-path',
            )
        }

        function hideDetails() {
            cy.nodes()
                .filter(
                    (node) =>
                        node.data(
                            'type',
                        ) ===
                            'version' ||
                        node.data(
                            'type',
                        ) ===
                            'engine_family',
                )
                .style('display', 'none')

            cy.edges()
                .filter(
                    (edge) =>
                        edge.data(
                            'type',
                        ) ===
                            'version' ||
                        edge.data(
                            'type',
                        ) ===
                            'engine',
                )
                .style('display', 'none')
        }

        function clearConnectionView() {
            restoreCenteredLayout()
            clearClasses()
            resetAnimatedDetails()

            cy.nodes()
                .filter(
                    (node) =>
                        node.data(
                            'type',
                        ) ===
                        'engine_family',
                )
                .style('display', 'none')

            cy.edges()
                .filter(
                    (edge) =>
                        edge.data(
                            'type',
                        ) ===
                        'engine',
                )
                .style('display', 'none')

            cy.nodes()
                .filter(
                    (node) =>
                        node.data(
                            'type',
                        ) ===
                        'version',
                )
                .forEach(
                    (version) => {
                        const variantId =
                            version.data(
                                'parent_variant_id',
                            ) as string

                        const edge =
                            cy.$id(
                                `version:${variantId}->${version.id()}`,
                            )

                        if (
                            expandedVariantsRef.current.has(
                                variantId,
                            )
                        ) {
                            version.style('display', 'element')
                            edge.style('display', 'element')
                        } else {
                            version.style('display', 'none')
                            edge.style('display', 'none')
                        }
                    },
                )
        }

        function showBaseUniverse() {
            restoreCenteredLayout()
            clearClasses()
            resetAnimatedDetails()

            expandedVariantsRef.current.clear()

            hideDetails()
        }

        function fitVisible() {
            const visible =
                cy.elements().filter(
                    (element) =>
                        element.visible(),
                )

            if (
                visible.length === 0
            ) {
                return
            }

            cy.animate({
                fit: {
                    eles:
                        visible,

                    padding:
                        90,
                },

                duration:
                    300,
            })
        }

        function expandVariant(
            variant:
                NodeSingular,
        ) {
            clearConnectionView()

            const variantId =
                variant.id()

            const versions =
                cy.nodes().filter(
                    (node) =>
                        node.data(
                            'type',
                        ) ===
                            'version' &&
                        node.data(
                            'parent_variant_id',
                        ) ===
                            variantId,
                )

            const isExpanded =
                expandedVariantsRef.current.has(
                    variantId,
                )

            const reducedMotion =
                prefersReducedMotion()

            const variantPosition =
                variant.position()

            const origin: Point = {
                x: variantPosition.x,
                y: variantPosition.y,
            }

            if (isExpanded) {
                expandedVariantsRef.current.delete(
                    variantId,
                )

                versions
                    .toArray()
                    .forEach(
                        (
                            versionElement,
                            index,
                        ) => {
                            const version =
                                versionElement as NodeSingular

                            const edge =
                                cy.$id(
                                    `version:${variantId}->${version.id()}`,
                                )

                            const final =
                                finalPosition(
                                    version.id(),
                                )

                            if (
                                final ===
                                null
                            ) {
                                return
                            }

                            version.stop()
                            edge.stop()

                            const delay =
                                reducedMotion
                                    ? 0
                                    : index *
                                      8

                            scheduleAnimation(
                                () => {
                                    if (
                                        reducedMotion
                                    ) {
                                        version.style('display', 'none')
                                        edge.style('display', 'none')

                                        version.position(
                                            final,
                                        )

                                        return
                                    }

                                    edge.animate(
                                        {
                                            style: {
                                                opacity:
                                                    0,
                                            },
                                        },
                                        {
                                            duration:
                                                120,

                                            easing:
                                                'ease-in',

                                            complete:
                                                () => {
                                                    edge.style('display', 'none')

                                                    edge.removeStyle(
                                                        'opacity',
                                                    )
                                                },
                                        },
                                    )

                                    const collapseStart =
                                        version.position()

                                    version.animate(
                                        {
                                            style: {
                                                opacity:
                                                    0,
                                            },
                                        },
                                        {
                                            duration:
                                                VERSION_COLLAPSE_DURATION,

                                            easing:
                                                'ease-in',
                                        },
                                    )

                                    animateNodePosition(
                                        version,
                                        collapseStart,
                                        origin,
                                        VERSION_COLLAPSE_DURATION,
                                        () => {
                                            version.style(
                                                'display',
                                                'none',
                                            )

                                            version.position(
                                                final,
                                            )

                                            version.removeStyle(
                                                'opacity',
                                            )
                                        },
                                    )
                                },
                                delay,
                            )
                        },
                    )

                setStatus(
                    `${variant.data('label')} collapsed`,
                )

                return
            }

            expandedVariantsRef.current.add(
                variantId,
            )

            versions
                .toArray()
                .forEach(
                    (
                        versionElement,
                        index,
                    ) => {
                        const version =
                            versionElement as NodeSingular

                        const edge =
                            cy.$id(
                                `version:${variantId}->${version.id()}`,
                            )

                        const final =
                            finalPosition(
                                version.id(),
                            )

                        if (
                            final === null
                        ) {
                            return
                        }

                        version.stop()
                        edge.stop()

                        version.position(
                            origin,
                        )

                        version.style(
                            'opacity',
                            0,
                        )

                        version.style('display', 'element')

                        edge.style(
                            'opacity',
                            0,
                        )

                        edge.style('display', 'element')

                        const delay =
                            reducedMotion
                                ? 0
                                : index *
                                  REVEAL_STAGGER

                        scheduleAnimation(
                            () => {
                                version.animate(
                                    {
                                        style: {
                                            opacity:
                                                1,
                                        },
                                    },
                                    {
                                        duration:
                                            reducedMotion
                                                ? 0
                                                : VERSION_EXPAND_DURATION,

                                        easing:
                                            'ease-out',

                                        complete:
                                            () => {
                                                version.removeStyle(
                                                    'opacity',
                                                )
                                            },
                                    },
                                )

                                animateNodePosition(
                                    version,
                                    origin,
                                    final,
                                    reducedMotion
                                        ? 0
                                        : VERSION_EXPAND_DURATION,
                                )

                                edge.animate(
                                    {
                                        style: {
                                            opacity:
                                                0.75,
                                        },
                                    },
                                    {
                                        duration:
                                            reducedMotion
                                                ? 0
                                                : 180,

                                        easing:
                                            'ease-out',

                                        complete:
                                            () => {
                                                edge.removeStyle(
                                                    'opacity',
                                                )
                                            },
                                    },
                                )
                            },
                            delay,
                        )
                    },
                )

            setStatus(
                `${variant.data('label')} versions revealed — click a version`,
            )
        }

        function revealVersionConnections(
            version:
                NodeSingular,
        ) {
            clearConnectionView()

            const sourceEngineEdges =
                cy.edges().filter(
                    (edge) =>
                        edge.data(
                            'type',
                        ) ===
                            'engine' &&
                        edge.data(
                            'source',
                        ) ===
                            version.id(),
                )

            const familyIds =
                sourceEngineEdges.map(
                    (edge) =>
                        edge.data(
                            'target',
                        ) as string,
                )

            const focusedIds =
                new Set<string>()

            focusedIds.add(
                version.id(),
            )

            const reducedMotion =
                prefersReducedMotion()

            const selectedVersionPosition =
                version.position()

            const selectedOrigin: Point = {
                x: selectedVersionPosition.x,
                y: selectedVersionPosition.y,
            }

            familyIds.forEach(
                (
                    familyId,
                    familyIndex,
                ) => {
                    const family =
                        cy.$id(
                            familyId,
                        )

                    const familyFinal =
                        finalPosition(
                            familyId,
                        )

                    if (
                        family.empty() ||
                        familyFinal ===
                            null
                    ) {
                        return
                    }

                    family.stop()

                    family.position(
                        selectedOrigin,
                    )

                    family.style(
                        'opacity',
                        0,
                    )

                    family.style('display', 'element')

                    focusedIds.add(
                        familyId,
                    )

                    const connectedEdges =
                        cy.edges().filter(
                            (edge) =>
                                edge.data(
                                    'type',
                                ) ===
                                    'engine' &&
                                edge.data(
                                    'target',
                                ) ===
                                    familyId,
                        )

                    connectedEdges.forEach(
                        (
                            edge,
                            edgeIndex,
                        ) => {
                            const connectedVersion =
                                cy.$id(
                                    edge.data(
                                        'source',
                                    ) as string,
                                )

                            const wasHidden =
                                connectedVersion.hidden()

                            const variantId =
                                connectedVersion.data(
                                    'parent_variant_id',
                                ) as string

                            const parentVariant =
                                cy.$id(
                                    variantId,
                                )

                            const versionFinal =
                                finalPosition(
                                    connectedVersion.id(),
                                )

                            if (
                                versionFinal ===
                                null
                            ) {
                                return
                            }

                            connectedVersion.stop()
                            edge.stop()

                            const versionEdge =
                                cy.$id(
                                    `version:${variantId}->${connectedVersion.id()}`,
                                )

                            versionEdge.stop()

                            if (
                                wasHidden
                            ) {
                                connectedVersion.position(
                                    parentVariant.position(),
                                )

                                connectedVersion.style(
                                    'opacity',
                                    0,
                                )

                                connectedVersion.style('display', 'element')

                                versionEdge.style(
                                    'opacity',
                                    0,
                                )

                                versionEdge.style('display', 'element')
                            }

                            edge.style(
                                'opacity',
                                0,
                            )

                            edge.style('display', 'element')

                            focusedIds.add(
                                edge.id(),
                            )

                            focusedIds.add(
                                connectedVersion.id(),
                            )

                            focusedIds.add(
                                versionEdge.id(),
                            )

                            const modelId =
                                connectedVersion.data(
                                    'parent_model_id',
                                ) as
                                    | string
                                    | null

                            const manufacturerId =
                                connectedVersion.data(
                                    'manufacturer_id',
                                ) as string

                            focusedIds.add(
                                variantId,
                            )

                            focusedIds.add(
                                manufacturerId,
                            )

                            if (
                                modelId ===
                                null
                            ) {
                                focusedIds.add(
                                    `hierarchy:${manufacturerId}->${variantId}`,
                                )
                            } else {
                                focusedIds.add(
                                    modelId,
                                )

                                focusedIds.add(
                                    `hierarchy:${manufacturerId}->${modelId}`,
                                )

                                focusedIds.add(
                                    `hierarchy:${modelId}->${variantId}`,
                                )
                            }

                            const baseDelay =
                                reducedMotion
                                    ? 0
                                    : familyIndex *
                                          80 +
                                      edgeIndex *
                                          28

                            if (
                                wasHidden
                            ) {
                                scheduleAnimation(
                                    () => {
                                        connectedVersion.animate(
                                            {
                                                style: {
                                                    opacity:
                                                        1,
                                                },
                                            },
                                            {
                                                duration:
                                                    reducedMotion
                                                        ? 0
                                                        : VERSION_EXPAND_DURATION,

                                                easing:
                                                    'ease-out',

                                                complete:
                                                    () => {
                                                        connectedVersion.removeStyle(
                                                            'opacity',
                                                        )
                                                    },
                                            },
                                        )

                                        animateNodePosition(
                                            connectedVersion,
                                            parentVariant.position(),
                                            versionFinal,
                                            reducedMotion
                                                ? 0
                                                : VERSION_EXPAND_DURATION,
                                        )

                                        versionEdge.animate(
                                            {
                                                style: {
                                                    opacity:
                                                        0.75,
                                                },
                                            },
                                            {
                                                duration:
                                                    reducedMotion
                                                        ? 0
                                                        : 180,

                                                easing:
                                                    'ease-out',

                                                complete:
                                                    () => {
                                                        versionEdge.removeStyle(
                                                            'opacity',
                                                        )
                                                    },
                                            },
                                        )
                                    },
                                    baseDelay,
                                )
                            }

                            scheduleAnimation(
                                () => {
                                    edge.animate(
                                        {
                                            style: {
                                                opacity:
                                                    0.75,
                                            },
                                        },
                                        {
                                            duration:
                                                reducedMotion
                                                    ? 0
                                                    : 190,

                                            easing:
                                                'ease-out',

                                            complete:
                                                () => {
                                                    edge.removeStyle(
                                                        'opacity',
                                                    )
                                                },
                                        },
                                    )
                                },
                                baseDelay +
                                    (reducedMotion
                                        ? 0
                                        : 130),
                            )
                        },
                    )

                    scheduleAnimation(
                        () => {
                            family.animate(
                                {
                                    style: {
                                        opacity:
                                            1,
                                    },
                                },
                                {
                                    duration:
                                        reducedMotion
                                            ? 0
                                            : CONNECTION_REVEAL_DURATION,

                                    easing:
                                        'ease-out',

                                    complete:
                                        () => {
                                            family.removeStyle(
                                                'opacity',
                                            )
                                        },
                                },
                            )

                            animateNodePosition(
                                family,
                                selectedOrigin,
                                familyFinal,
                                reducedMotion
                                    ? 0
                                    : CONNECTION_REVEAL_DURATION,
                            )
                        },
                        reducedMotion
                            ? 0
                            : 90 +
                              familyIndex *
                                  80,
                    )
                },
            )

            sourceEngineEdges.style('display', 'element')

            sourceEngineEdges.forEach(
                (edge) => {
                    focusedIds.add(
                        edge.id(),
                    )
                },
            )

            cy.elements().addClass(
                'dimmed',
            )

            for (const id of
                focusedIds) {
                cy.$id(id)
                    .removeClass(
                        'dimmed',
                    )
                    .addClass(
                        'focused',
                    )
            }

            setStatus(
                `${version.data('label')} connections revealed`,
            )
        }

        function showShortestRoutes(
            startId: string,
            endId: string,
        ) {
            showBaseUniverse()

            const routes =
                buildShortestRoutes(
                    graph!,
                    startId,
                    endId,
                )

            setRouteResult({
                startId,
                endId,
                routes,
            })

            if (
                routes.length === 0
            ) {
                cy.$id(
                    startId,
                ).addClass(
                    'route-start',
                )

                cy.$id(
                    endId,
                ).addClass(
                    'route-end',
                )

                setStatus(
                    'No discovered path found',
                )

                return
            }

            const focused =
                new Set<string>()

            for (const route of
                routes) {
                for (const nodeId of
                    route.nodeIds) {
                    focused.add(
                        nodeId,
                    )

                    cy.$id(
                        nodeId,
                    ).style('display', 'element')
                }

                for (const edgeId of
                    route.edgeIds) {
                    focused.add(
                        edgeId,
                    )

                    cy.$id(
                        edgeId,
                    ).style('display', 'element')
                }
            }

            cy.elements().addClass(
                'dimmed',
            )

            for (const id of
                focused) {
                cy.$id(id)
                    .removeClass(
                        'dimmed',
                    )
                    .addClass(
                        'focused route-path',
                    )
            }

            cy.$id(startId)
                .removeClass(
                    'dimmed',
                )
                .addClass(
                    'route-start',
                )

            cy.$id(endId)
                .removeClass(
                    'dimmed',
                )
                .addClass(
                    'route-end',
                )

            setStatus(
                `${routes.length} shortest discovered path${routes.length === 1 ? '' : 's'}`,
            )

            window.setTimeout(
                fitVisible,
                40,
            )
        }

        showBaseUniverse()

        if (
            graph.nodes.length >
            0
        ) {
            fitVisible()
        }

        /*
         * One-shot unlock moment.
         *
         * localStorage stores the correctly guessed Version ID.
         * The graph API expands that Version to its whole Variant,
         * so we find the returned Version and pulse/focus its parent
         * Variant when the Universe is opened.
         */
        if (
            newlyUnlockedVehicleId !==
            null
        ) {
            const unlockedVersion =
                graph.nodes.find(
                    (node) =>
                        node.type ===
                            'version' &&
                        node.entity_id ===
                            newlyUnlockedVehicleId,
                )

            const unlockedVariant =
                unlockedVersion
                    ?.parent_variant_id ===
                null
                    ? undefined
                    : graph.nodes.find(
                          (node) =>
                              node.id ===
                              unlockedVersion
                                  ?.parent_variant_id,
                      )

            if (
                unlockedVariant !==
                undefined
            ) {
                const target =
                    cy.$id(
                        unlockedVariant.id,
                    )

                const reducedMotion =
                    prefersReducedMotion()

                scheduleUnlockAnimation(
                    () => {
                        target.addClass(
                            'newly-unlocked',
                        )

                        setStatus(
                            `${unlockedVariant.label} unlocked`,
                        )

                        if (
                            !reducedMotion
                        ) {
                            const targetZoom =
                                Math.max(
                                    cy.zoom(),
                                    0.82,
                                )

                            cy.animate({
                                center: {
                                    eles:
                                        target,
                                },

                                zoom:
                                    targetZoom,

                                duration:
                                    420,
                            })

                            target
                                .stop()
                                .animate(
                                    {
                                        style: {
                                            'border-width':
                                                9,
                                        },
                                    },
                                    {
                                        duration:
                                            330,
                                    },
                                )
                                .animate(
                                    {
                                        style: {
                                            'border-width':
                                                2,
                                        },
                                    },
                                    {
                                        duration:
                                            330,
                                    },
                                )
                                .animate(
                                    {
                                        style: {
                                            'border-width':
                                                9,
                                        },
                                    },
                                    {
                                        duration:
                                            330,
                                    },
                                )
                                .animate(
                                    {
                                        style: {
                                            'border-width':
                                                2,
                                        },
                                    },
                                    {
                                        duration:
                                            330,
                                    },
                                )
                        }

                        scheduleUnlockAnimation(
                            () => {
                                target.removeClass(
                                    'newly-unlocked',
                                )

                                target.removeStyle(
                                    'border-width',
                                )

                                setStatus(
                                    'Base universe — click a node',
                                )

                                onUnlockAnimationCompleteRef.current(
                                    newlyUnlockedVehicleId,
                                )
                            },
                            reducedMotion
                                ? 650
                                : UNLOCK_PULSE_DURATION,
                        )
                    },
                    reducedMotion
                        ? 0
                        : 360,
                )
            } else {
                onUnlockAnimationCompleteRef.current(
                    newlyUnlockedVehicleId,
                )
            }
        }

        cy.on(
            'tapstart',
            (event) => {
                if (
                    event.target ===
                    cy
                ) {
                    canvasMovedRef.current =
                        false
                }
            },
        )

        cy.on(
            'pan',
            () => {
                canvasMovedRef.current =
                    true
            },
        )

        cy.on(
            'tap',
            'node',
            (event) => {
                const node =
                    event.target

                setSelectedNodeId(
                    node.id(),
                )

                if (
                    routeModeRef.current
                ) {
                    const startId =
                        routeStartRef.current

                    if (
                        startId ===
                        null
                    ) {
                        clearConnectionView()

                        routeStartRef.current =
                            node.id()

                        node.addClass(
                            'route-start',
                        )

                        setRouteResult(
                            null,
                        )

                        setStatus(
                            `${node.data('label')} → select destination`,
                        )

                        return
                    }

                    if (
                        startId ===
                        node.id()
                    ) {
                        setStatus(
                            'Choose a different destination',
                        )

                        return
                    }

                    showShortestRoutes(
                        startId,
                        node.id(),
                    )

                    routeStartRef.current =
                        null

                    setSelectedNodeId(
                        null,
                    )

                    return
                }

                const type =
                    node.data(
                        'type',
                    ) as UniverseNode['type']

                setRouteResult(
                    null,
                )

                if (
                    type ===
                    'variant'
                ) {
                    expandVariant(
                        node,
                    )

                    return
                }

                if (
                    type ===
                    'version'
                ) {
                    revealVersionConnections(
                        node,
                    )

                    return
                }

                setStatus(
                    `${node.data('label')} selected`,
                )
            },
        )

        cy.on(
            'tap',
            (event) => {
                if (
                    event.target !==
                        cy ||
                    routeModeRef.current ||
                    canvasMovedRef.current
                ) {
                    return
                }

                clearConnectionView()

                setSelectedNodeId(
                    null,
                )

                setRouteResult(
                    null,
                )

                setStatus(
                    'Base universe — click a node',
                )
            },
        )

        const resizeObserver =
            new ResizeObserver(
                () => {
                    cy.resize()
                },
            )

        resizeObserver.observe(
            graphRef.current,
        )

        actionsRef.current = {
            fitVisible,

            centerSelected:
                (nodeId) => {
                    const node =
                        cy.$id(
                            nodeId,
                        )

                    if (
                        node.empty()
                    ) {
                        return
                    }

                    const type =
                        node.data(
                            'type',
                        ) as UniverseNode['type']

                    if (
                        type ===
                        'engine_family'
                    ) {
                        centerEngineFamily(
                            node as unknown as NodeSingular,
                        )

                        return
                    }

                    /*
                     * For ordinary nodes the button still behaves as a
                     * useful "focus" command. The semantic radial relayout
                     * is intentionally reserved for Engine families because
                     * they are the many-to-many connection hubs.
                     */
                    cy.animate({
                        center: {
                            eles:
                                node,
                        },

                        zoom:
                            Math.max(
                                cy.zoom(),
                                1,
                            ),

                        duration:
                            300,
                    })

                    setStatus(
                        `${node.data('label')} centered`,
                    )
                },

            clearConnectionView,

            showBaseUniverse:
                () => {
                    showBaseUniverse()

                    setSelectedNodeId(
                        null,
                    )

                    setRouteResult(
                        null,
                    )
                },

            showAllVersions:
                () => {
                    clearClasses()
                    resetAnimatedDetails()

                    cy.nodes()
                        .filter(
                            (node) =>
                                node.data(
                                    'type',
                                ) ===
                                'version',
                        )
                        .style('display', 'element')

                    cy.edges()
                        .filter(
                            (edge) =>
                                edge.data(
                                    'type',
                                ) ===
                                'version',
                        )
                        .style('display', 'element')

                    cy.nodes()
                        .filter(
                            (node) =>
                                node.data(
                                    'type',
                                ) ===
                                'engine_family',
                        )
                        .style('display', 'none')

                    cy.edges()
                        .filter(
                            (edge) =>
                                edge.data(
                                    'type',
                                ) ===
                                'engine',
                        )
                        .style('display', 'none')

                    expandedVariantsRef.current =
                        new Set(
                            graph.nodes
                                .filter(
                                    (
                                        node,
                                    ) =>
                                        node.type ===
                                        'variant',
                                )
                                .map(
                                    (
                                        node,
                                    ) =>
                                        node.id,
                                ),
                        )
                },

            showAllConnections:
                () => {
                    clearClasses()
                    resetAnimatedDetails()

                    cy.elements().style('display', 'element')

                    expandedVariantsRef.current =
                        new Set(
                            graph.nodes
                                .filter(
                                    (
                                        node,
                                    ) =>
                                        node.type ===
                                        'variant',
                                )
                                .map(
                                    (
                                        node,
                                    ) =>
                                        node.id,
                                ),
                        )
                },
        }

        return () => {
            resizeObserver.disconnect()

            clearDetailAnimationTimeouts()
            clearUnlockAnimationTimeouts()
            clearPositionAnimations()
            centeredNodeIdsRef.current.clear()

            actionsRef.current =
                null

            cy.destroy()

            cyRef.current =
                null
        }
    }, [graph])

    function handleBaseView() {
        actionsRef.current
            ?.showBaseUniverse()

        expandedVariantsRef.current.clear()

        routeStartRef.current =
            null

        setSelectedNodeId(
            null,
        )

        setRouteResult(
            null,
        )

        setStatus(
            'Base universe — click a node',
        )
    }

    function handleAllVersions() {
        actionsRef.current
            ?.showAllVersions()

        setSelectedNodeId(
            null,
        )

        setRouteResult(
            null,
        )

        setStatus(
            'All discovered versions revealed',
        )
    }

    function handleAllConnections() {
        actionsRef.current
            ?.showAllConnections()

        setSelectedNodeId(
            null,
        )

        setRouteResult(
            null,
        )

        setStatus(
            'All discovered connections revealed',
        )
    }

    function toggleRouteMode() {
        const next =
            !routeMode

        setRouteMode(next)

        routeModeRef.current =
            next

        routeStartRef.current =
            null

        setSelectedNodeId(
            null,
        )

        setRouteResult(
            null,
        )

        actionsRef.current
            ?.showBaseUniverse()

        setStatus(
            next
                ? 'Connection finder — select starting node'
                : 'Base universe — click a node',
        )
    }

    const floatingButtonStyle = {
        width: '44px',
        height: '44px',

        border:
            '1px solid rgba(255,255,255,0.09)',

        borderRadius: '12px',

        background:
            'rgba(23,26,32,0.88)',

        color: '#dfe3e8',

        fontSize: '18px',

        cursor: 'pointer',

        boxShadow:
            '0 8px 24px rgba(0,0,0,0.28)',

        backdropFilter:
            'blur(12px)',
    }

    const menuButtonStyle = {
        width: '100%',

        padding: '11px 12px',

        border:
            '1px solid rgba(255,255,255,0.07)',

        borderRadius: '9px',

        background:
            '#191d24',

        color: '#e5e7eb',

        textAlign:
            'left' as const,

        fontSize: '14px',

        fontWeight: 500,

        cursor: 'pointer',
    }

    return (
        <section className="universe-page">
            <div
                className="universe-canvas"
                ref={graphRef}
            />

            <div className="universe-title">
                <strong>
                    Automotive
                    Universe
                </strong>

                <span>
                    {status}
                </span>
            </div>

            <div className="universe-controls">
                <button
                    onClick={() =>
                        actionsRef.current
                            ?.fitVisible()
                    }
                    title="Fit graph"
                    aria-label="Fit graph"
                    style={
                        floatingButtonStyle
                    }
                >
                    ⛶
                </button>

                <button
                    onClick={() => {
                        if (
                            selectedNodeId ===
                            null
                        ) {
                            return
                        }

                        actionsRef.current
                            ?.centerSelected(
                                selectedNodeId,
                            )
                    }}
                    title={
                        selectedNodeId ===
                        null
                            ? 'Select a node to center'
                            : 'Center on selection'
                    }
                    aria-label="Center on selection"
                    disabled={
                        selectedNodeId ===
                        null
                    }
                    style={{
                        ...floatingButtonStyle,

                        opacity:
                            selectedNodeId ===
                            null
                                ? 0.38
                                : 1,

                        cursor:
                            selectedNodeId ===
                            null
                                ? 'default'
                                : 'pointer',
                    }}
                >
                    ◎
                </button>

                <button
                    onClick={
                        toggleRouteMode
                    }
                    title="Find connections"
                    aria-label="Find connections"
                    style={{
                        ...floatingButtonStyle,

                        background:
                            routeMode
                                ? '#3a4d60'
                                : 'rgba(23,26,32,0.88)',
                    }}
                >
                    ⇄
                </button>

                <button
                    onClick={() =>
                        setControlsOpen(
                            (
                                value,
                            ) =>
                                !value,
                        )
                    }
                    title="View options"
                    aria-label="View options"
                    style={{
                        ...floatingButtonStyle,

                        background:
                            controlsOpen
                                ? '#343a45'
                                : 'rgba(23,26,32,0.88)',
                    }}
                >
                    ⚙
                </button>
            </div>

            {controlsOpen && (
                <div className="universe-menu">
                    <div className="universe-menu-label">
                        View
                    </div>

                    <button
                        style={
                            menuButtonStyle
                        }
                        onClick={() => {
                            handleBaseView()

                            setControlsOpen(
                                false,
                            )
                        }}
                    >
                        Base universe
                    </button>

                    <button
                        style={
                            menuButtonStyle
                        }
                        onClick={() => {
                            handleAllVersions()

                            setControlsOpen(
                                false,
                            )
                        }}
                    >
                        Reveal all
                        versions
                    </button>

                    <button
                        style={
                            menuButtonStyle
                        }
                        onClick={() => {
                            handleAllConnections()

                            setControlsOpen(
                                false,
                            )
                        }}
                    >
                        Reveal all
                        connections
                    </button>

                    <div className="universe-menu-divider" />

                    <div className="universe-legend">
                        <span>
                            ● Manufacturer
                        </span>

                        <span>
                            ▰ Model
                        </span>

                        <span>
                            ● Variant
                        </span>

                        <span>
                            ▰ Version
                        </span>

                        <span>
                            ◆ Engine
                            family
                        </span>
                    </div>
                </div>
            )}

            {isLoading && (
                <div className="universe-message">
                    Loading
                    universe...
                </div>
            )}

            {error !== null && (
                <div className="universe-message universe-error">
                    {error}
                </div>
            )}

            {!isLoading &&
                error === null &&
                graph !== null &&
                graph.nodes.length ===
                    0 && (
                    <div className="universe-message">
                        Your Automotive
                        Universe is empty.
                        Discover a car in
                        Cardle to grow it.
                    </div>
                )}

            {routeResult !==
                null && (
                <div className="universe-info-panel">
                    <button
                        className="universe-panel-close"
                        onClick={() =>
                            setRouteResult(
                                null,
                            )
                        }
                        aria-label="Close path results"
                    >
                        ×
                    </button>

                    <div className="universe-panel-kicker">
                        Shortest paths
                    </div>

                    <h2>
                        {
                            nodesById.get(
                                routeResult.startId,
                            )?.label
                        }{' '}
                        ↔{' '}
                        {
                            nodesById.get(
                                routeResult.endId,
                            )?.label
                        }
                    </h2>

                    {routeResult.routes
                        .length ===
                    0 ? (
                        <p className="universe-panel-muted">
                            No discovered
                            connection.
                        </p>
                    ) : (
                        <>
                            <p className="universe-panel-muted">
                                {
                                    routeResult
                                        .routes
                                        .length
                                }{' '}
                                shortest
                                discovered
                                path
                                {routeResult
                                    .routes
                                    .length ===
                                1
                                    ? ''
                                    : 's'}
                            </p>

                            <div className="universe-route-list">
                                {routeResult.routes
                                    .slice(
                                        0,
                                        6,
                                    )
                                    .map(
                                        (
                                            route,
                                            index,
                                        ) => (
                                            <div
                                                className="universe-route"
                                                key={`${routeResult.startId}-${routeResult.endId}-${index}`}
                                            >
                                                {route.nodeIds
                                                    .map(
                                                        (
                                                            nodeId,
                                                        ) =>
                                                            nodesById.get(
                                                                nodeId,
                                                            )
                                                                ?.label ??
                                                            nodeId,
                                                    )
                                                    .join(
                                                        ' → ',
                                                    )}
                                            </div>
                                        ),
                                    )}
                            </div>

                            {routeResult.routes
                                .length >
                                6 && (
                                <p className="universe-panel-muted">
                                    +
                                    {routeResult
                                        .routes
                                        .length -
                                        6}{' '}
                                    more
                                </p>
                            )}
                        </>
                    )}
                </div>
            )}

            {routeResult ===
                null &&
                selectedInfo !==
                    null && (
                    <div className="universe-info-panel">
                        <button
                            className="universe-panel-close"
                            onClick={() =>
                                setSelectedNodeId(
                                    null,
                                )
                            }
                            aria-label="Close information"
                        >
                            ×
                        </button>

                        <div className="universe-panel-kicker">
                            {
                                selectedInfo.type
                            }
                        </div>

                        <h2>
                            {
                                selectedInfo.title
                            }
                        </h2>

                        {selectedInfo.subtitle && (
                            <p className="universe-panel-muted">
                                {
                                    selectedInfo.subtitle
                                }
                            </p>
                        )}

                        {selectedInfo.rows
                            .length >
                            0 && (
                            <dl className="universe-info-rows">
                                {selectedInfo.rows.map(
                                    (
                                        row,
                                    ) => (
                                        <div
                                            key={
                                                row.label
                                            }
                                        >
                                            <dt>
                                                {
                                                    row.label
                                                }
                                            </dt>

                                            <dd>
                                                {
                                                    row.value
                                                }
                                            </dd>
                                        </div>
                                    ),
                                )}
                            </dl>
                        )}
                    </div>
                )}
        </section>
    )
}

export default AutomotiveUniverse