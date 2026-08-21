import type { VehicleSearchResult } from '../types/game'


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
    const hasSearchQuery =
        query.trim().length >= 2

    const noResults =
        hasSearchQuery &&
        !isSearching &&
        results.length === 0

    return (
        <section className="vehicle-search">
            <div className="search-container">
                {results.length > 0 && (
                    <div className="search-results">
                        {results.map((vehicle) => {
                            const alreadyGuessed =
                                guessedIds.includes(
                                    vehicle.id
                                )

                            return (
                                <button
                                    key={vehicle.id}
                                    className="search-result"
                                    onClick={() =>
                                        onGuess(vehicle.id)
                                    }
                                    disabled={
                                        alreadyGuessed ||
                                        gameFinished ||
                                        isSubmitting
                                    }
                                >
                                    <span>
                                        {vehicle.display_name}
                                    </span>

                                    {alreadyGuessed && (
                                        <span className="already-guessed">
                                            Guessed
                                        </span>
                                    )}
                                </button>
                            )
                        })}
                    </div>
                )}

                {isSearching && (
                    <div className="search-status">
                        Searching...
                    </div>
                )}

                {noResults && (
                    <div className="search-status">
                        No cars found
                    </div>
                )}

                <input
                    className="search-input"
                    type="text"
                    value={query}
                    onChange={(event) =>
                        onQueryChange(
                            event.target.value
                        )
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