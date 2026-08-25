import {
    useEffect,
    useRef,
    useState,
} from 'react'

import type {
    VehicleSearchResult,
} from '../types/game'


type VehicleSearchProps = {
    query: string
    results: VehicleSearchResult[]
    guessedIds: string[]

    gameFinished: boolean
    isSearching: boolean
    isSubmitting: boolean

    onQueryChange: (query: string) => void
    onGuess: (vehicleId: string) => void
}


type DropdownDirection =
    | 'down'
    | 'up'


function VehicleSearch({
    query,
    results,
    guessedIds,
    gameFinished,
    isSearching,
    isSubmitting,
    onQueryChange,
    onGuess,
}: VehicleSearchProps) {
    const searchRef =
        useRef<HTMLElement | null>(
            null,
        )

    const searchContainerRef =
        useRef<HTMLDivElement | null>(
            null,
        )

    const [isOpen, setIsOpen] =
        useState(true)

    const [
        dropdownDirection,
        setDropdownDirection,
    ] = useState<DropdownDirection>(
        'down',
    )

    const [
        dropdownMaxHeight,
        setDropdownMaxHeight,
    ] = useState(300)


    const hasSearchQuery =
        query.trim().length >= 2

    const noResults =
        hasSearchQuery &&
        !isSearching &&
        results.length === 0


    /*
     * Close the dropdown when the user clicks
     * anywhere outside the search component.
     */
    useEffect(() => {
        function handlePointerDown(
            event: PointerEvent,
        ) {
            const target =
                event.target as Node

            if (
                searchRef.current &&
                !searchRef.current.contains(
                    target,
                )
            ) {
                setIsOpen(false)
            }
        }

        document.addEventListener(
            'pointerdown',
            handlePointerDown,
        )

        return () => {
            document.removeEventListener(
                'pointerdown',
                handlePointerDown,
            )
        }
    }, [])


    /*
     * Decide whether the dropdown should open
     * downward or upward.
     *
     * Downward is preferred.
     *
     * It only flips upward when there is not
     * enough room below and there is more room
     * available above.
     */
    useEffect(() => {
        if (!isOpen) {
            return
        }

        function updateDropdownPosition() {
            const container =
                searchContainerRef.current

            if (!container) {
                return
            }

            const rect =
                container.getBoundingClientRect()

            const gap = 6
            const normalMaxHeight = 300

            const estimatedDropdownHeight =
                results.length > 0
                    ? Math.min(
                          normalMaxHeight,
                          results.length * 49,
                      )
                    : 48

            const spaceBelow =
                window.innerHeight -
                rect.bottom -
                gap

            const spaceAbove =
                rect.top -
                gap

            const shouldOpenUp =
                spaceBelow <
                    estimatedDropdownHeight &&
                spaceAbove >
                    spaceBelow

            const direction:
                DropdownDirection =
                    shouldOpenUp
                        ? 'up'
                        : 'down'

            const availableSpace =
                direction === 'up'
                    ? spaceAbove
                    : spaceBelow

            setDropdownDirection(
                direction,
            )

            setDropdownMaxHeight(
                Math.min(
                    normalMaxHeight,
                    Math.max(
                        80,
                        availableSpace - 8,
                    ),
                ),
            )
        }

        const animationFrame =
            requestAnimationFrame(
                updateDropdownPosition,
            )

        window.addEventListener(
            'resize',
            updateDropdownPosition,
        )

        window.addEventListener(
            'scroll',
            updateDropdownPosition,
            true,
        )

        return () => {
            cancelAnimationFrame(
                animationFrame,
            )

            window.removeEventListener(
                'resize',
                updateDropdownPosition,
            )

            window.removeEventListener(
                'scroll',
                updateDropdownPosition,
                true,
            )
        }
    }, [
        isOpen,
        results.length,
        isSearching,
        query,
    ])


    function handleQueryChange(
        value: string,
    ) {
        setIsOpen(true)

        onQueryChange(
            value,
        )
    }


    function handleFocus() {
        if (hasSearchQuery) {
            setIsOpen(true)
        }
    }


    const dropdownPosition =
        dropdownDirection === 'down'
            ? {
                  top: 'calc(100% + 6px)',
                  bottom: 'auto',
              }
            : {
                  top: 'auto',
                  bottom: 'calc(100% + 6px)',
              }


    return (
        <section
            className="vehicle-search"
            ref={searchRef}
        >
            <div
                className="search-container"
                ref={searchContainerRef}
            >
                {isOpen &&
                    results.length > 0 && (
                        <div
                            className="search-results"
                            style={{
                                ...dropdownPosition,
                                maxHeight:
                                    `${dropdownMaxHeight}px`,
                            }}
                        >
                            {results.map(
                                (vehicle) => {
                                    const alreadyGuessed =
                                        guessedIds.includes(
                                            vehicle.id,
                                        )

                                    return (
                                        <button
                                            key={
                                                vehicle.id
                                            }
                                            className="search-result"
                                            onClick={() =>
                                                onGuess(
                                                    vehicle.id,
                                                )
                                            }
                                            disabled={
                                                alreadyGuessed ||
                                                gameFinished ||
                                                isSubmitting
                                            }
                                        >
                                            <span>
                                                {
                                                    vehicle.display_name
                                                }
                                            </span>

                                            {alreadyGuessed && (
                                                <span className="already-guessed">
                                                    Guessed
                                                </span>
                                            )}
                                        </button>
                                    )
                                },
                            )}
                        </div>
                    )}

                {isOpen &&
                    isSearching && (
                        <div
                            className="search-status"
                            style={
                                dropdownPosition
                            }
                        >
                            Searching...
                        </div>
                    )}

                {isOpen &&
                    noResults && (
                        <div
                            className="search-status"
                            style={
                                dropdownPosition
                            }
                        >
                            No cars found
                        </div>
                    )}

                <input
                    className="search-input"
                    type="text"
                    value={query}
                    onChange={(event) =>
                        handleQueryChange(
                            event.target.value,
                        )
                    }
                    onFocus={
                        handleFocus
                    }
                    placeholder={
                        isSubmitting
                            ? 'Submitting guess...'
                            : 'Search for a car...'
                    }
                    disabled={
                        gameFinished ||
                        isSubmitting
                    }
                />
            </div>
        </section>
    )
}


export default VehicleSearch