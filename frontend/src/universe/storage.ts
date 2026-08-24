const UNIVERSE_STORAGE_KEY =
    'cardle-universe-unlocks-v2'

const PENDING_UNLOCK_ANIMATION_KEY =
    'cardle-universe-pending-unlock-v1'

type SavedUniverse = {
    vehicle_ids: string[]
}


export function loadUnlockedVehicleIds(): string[] {
    const savedText =
        localStorage.getItem(
            UNIVERSE_STORAGE_KEY,
        )

    if (savedText === null) {
        return []
    }

    try {
        const saved = JSON.parse(
            savedText,
        ) as SavedUniverse

        if (
            !Array.isArray(
                saved.vehicle_ids,
            )
        ) {
            return []
        }

        return [
            ...new Set(
                saved.vehicle_ids.filter(
                    (
                        value,
                    ): value is string =>
                        typeof value ===
                            'string' &&
                        value.length > 0,
                ),
            ),
        ]
    } catch {
        return []
    }
}


export function loadPendingUniverseUnlockId():
    | string
    | null {
    const value =
        localStorage.getItem(
            PENDING_UNLOCK_ANIMATION_KEY,
        )

    if (
        value === null ||
        value.length === 0
    ) {
        return null
    }

    return value
}


export function clearPendingUniverseUnlockId(
    vehicleId?: string,
): void {
    if (vehicleId !== undefined) {
        const current =
            loadPendingUniverseUnlockId()

        if (current !== vehicleId) {
            return
        }
    }

    localStorage.removeItem(
        PENDING_UNLOCK_ANIMATION_KEY,
    )
}


export function unlockVehicleIds(
    vehicleIds: string[],
): string[] {
    const current =
        loadUnlockedVehicleIds()

    const validVehicleIds =
        vehicleIds.filter(
            (value) =>
                value.length > 0,
        )

    const currentSet =
        new Set(current)

    const newlyUnlocked =
        validVehicleIds.filter(
            (vehicleId) =>
                !currentSet.has(
                    vehicleId,
                ),
        )

    const next = [
        ...new Set([
            ...current,
            ...validVehicleIds,
        ]),
    ]

    localStorage.setItem(
        UNIVERSE_STORAGE_KEY,
        JSON.stringify({
            vehicle_ids: next,
        } satisfies SavedUniverse),
    )

    /*
     * Cardle can unlock at most one new daily target, but using
     * the last ID here keeps the helper safe if that ever changes.
     */
    const newest =
        newlyUnlocked.at(-1)

    if (newest !== undefined) {
        localStorage.setItem(
            PENDING_UNLOCK_ANIMATION_KEY,
            newest,
        )
    }

    return next
}
