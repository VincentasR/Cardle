import {
    useEffect,
    useState,
} from 'react'

import Header from './components/Header'
import GuessBoard from './components/GuessBoard'
import VehicleSearch from './components/VehicleSearch'
import HowToPlay from './components/HowToPlay'
import AutomotiveUniverse from './components/AutomotiveUniverse'

import type {
    GameState,
    SavedGame,
    VehicleSearchResult,
} from './types/game'

import {
    clearPendingUniverseUnlockId,
    loadPendingUniverseUnlockId,
    loadUnlockedVehicleIds,
    unlockVehicleIds,
} from './universe/storage'


const STORAGE_KEY =
    'cardle-daily-game'


type AppView =
    | 'game'
    | 'graph'


function viewFromHash(): AppView {
    return window.location.hash ===
        '#graph'
        ? 'graph'
        : 'game'
}


function App() {
    const [view, setView] =
        useState<AppView>(
            viewFromHash,
        )

    const [
        unlockedVehicleIds,
        setUnlockedVehicleIds,
    ] = useState<string[]>(
        loadUnlockedVehicleIds,
    )

    const [
        pendingUniverseUnlockId,
        setPendingUniverseUnlockId,
    ] = useState<string | null>(
        loadPendingUniverseUnlockId,
    )

    const [query, setQuery] =
        useState('')

    const [results, setResults] =
        useState<
            VehicleSearchResult[]
        >([])

    const [
        guessedIds,
        setGuessedIds,
    ] = useState<string[]>([])

    const [
        gameState,
        setGameState,
    ] =
        useState<GameState | null>(
            null,
        )

    const [
        isLoadingGame,
        setIsLoadingGame,
    ] = useState(true)

    const [
        isSearching,
        setIsSearching,
    ] = useState(false)

    const [
        isSubmitting,
        setIsSubmitting,
    ] = useState(false)

    const [error, setError] =
        useState<string | null>(
            null,
        )

    const [
        showRules,
        setShowRules,
    ] = useState(false)


    function saveUnlocks(
        vehicleIds: string[],
    ) {
        if (
            vehicleIds.length === 0
        ) {
            return
        }

        const next =
            unlockVehicleIds(
                vehicleIds,
            )

        setUnlockedVehicleIds(
            next,
        )

        setPendingUniverseUnlockId(
            loadPendingUniverseUnlockId(),
        )
    }


    function openGraph() {
        window.location.hash =
            'graph'
    }


    function openGame() {
        history.pushState(
            null,
            '',
            window.location.pathname +
                window.location.search,
        )

        setView('game')
    }


    useEffect(() => {
        function handleHashChange() {
            setView(
                viewFromHash(),
            )
        }

        window.addEventListener(
            'hashchange',
            handleHashChange,
        )

        return () => {
            window.removeEventListener(
                'hashchange',
                handleHashChange,
            )
        }
    }, [])


    /*
     * Restore today's game when the page first loads.
     */
    useEffect(() => {
        async function restoreGame() {
            try {
                setError(null)

                const response =
                    await fetch(
                        '/api/game/today/state',
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type':
                                    'application/json',
                            },
                            body: JSON.stringify(
                                {
                                    guess_ids: [],
                                },
                            ),
                        },
                    )

                if (!response.ok) {
                    throw new Error(
                        'Could not load today\'s Cardle.',
                    )
                }

                const emptyGame: GameState =
                    await response.json()

                const savedText =
                    localStorage.getItem(
                        STORAGE_KEY,
                    )

                if (
                    savedText === null
                ) {
                    setGameState(
                        emptyGame,
                    )
                    return
                }

                const savedGame: SavedGame =
                    JSON.parse(
                        savedText,
                    )

                if (
                    savedGame.date !==
                    emptyGame.date
                ) {
                    localStorage.removeItem(
                        STORAGE_KEY,
                    )

                    setGuessedIds([])
                    setGameState(
                        emptyGame,
                    )

                    return
                }

                if (
                    savedGame.guess_ids
                        .length === 0
                ) {
                    setGameState(
                        emptyGame,
                    )
                    return
                }

                const restoreResponse =
                    await fetch(
                        '/api/game/today/state',
                        {
                            method:
                                'POST',
                            headers: {
                                'Content-Type':
                                    'application/json',
                            },
                            body: JSON.stringify(
                                {
                                    guess_ids:
                                        savedGame.guess_ids,
                                },
                            ),
                        },
                    )

                if (
                    !restoreResponse.ok
                ) {
                    throw new Error(
                        'Could not restore your saved game.',
                    )
                }

                const restoredGame: GameState =
                    await restoreResponse.json()

                setGuessedIds(
                    savedGame.guess_ids,
                )

                setGameState(
                    restoredGame,
                )

                /*
                 * Automotive Universe progression:
                 *
                 * Only a CORRECT daily answer unlocks a car.
                 * Wrong guesses never unlock anything, and losing
                 * the daily game does not unlock the revealed target.
                 *
                 * On restore, re-add today's target only if this
                 * saved game was actually won.
                 */
                if (
                    restoredGame.won &&
                    restoredGame.target !==
                        null
                ) {
                    saveUnlocks([
                        restoredGame.target.id,
                    ])
                }
            } catch (restoreError) {
                console.error(
                    restoreError,
                )

                setError(
                    'Cardle could not connect to the server.',
                )
            } finally {
                setIsLoadingGame(
                    false,
                )
            }
        }

        restoreGame()
    }, [])


    /*
     * Automatically search while the user types.
     */
    useEffect(() => {
        if (
            gameState?.finished
        ) {
            setResults([])
            setIsSearching(false)
            return
        }

        const trimmedQuery =
            query.trim()

        if (
            trimmedQuery.length < 2
        ) {
            setResults([])
            setIsSearching(false)
            return
        }

        const controller =
            new AbortController()

        setIsSearching(true)
        setError(null)

        const timeoutId =
            setTimeout(
                async () => {
                    try {
                        const response =
                            await fetch(
                                `/api/vehicles/search?q=${encodeURIComponent(trimmedQuery)}`,
                                {
                                    signal:
                                        controller.signal,
                                },
                            )

                        if (
                            !response.ok
                        ) {
                            throw new Error(
                                'Vehicle search failed.',
                            )
                        }

                        const data: VehicleSearchResult[] =
                            await response.json()

                        setResults(
                            data,
                        )
                    } catch (searchError) {
                        if (
                            searchError instanceof
                                Error &&
                            searchError.name ===
                                'AbortError'
                        ) {
                            return
                        }

                        console.error(
                            searchError,
                        )

                        setResults([])

                        setError(
                            'Could not search for vehicles.',
                        )
                    } finally {
                        if (
                            !controller.signal
                                .aborted
                        ) {
                            setIsSearching(
                                false,
                            )
                        }
                    }
                },
                250,
            )

        return () => {
            clearTimeout(
                timeoutId,
            )

            controller.abort()
        }
    }, [
        query,
        gameState?.finished,
    ])


    async function submitGuess(
        vehicleId: string,
    ) {
        if (
            isSubmitting ||
            gameState?.finished
        ) {
            return
        }

        const nextGuessIds = [
            ...guessedIds,
            vehicleId,
        ]

        try {
            setIsSubmitting(true)
            setError(null)

            const response =
                await fetch(
                    '/api/game/today/state',
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type':
                                'application/json',
                        },
                        body: JSON.stringify(
                            {
                                guess_ids:
                                    nextGuessIds,
                            },
                        ),
                    },
                )

            if (!response.ok) {
                throw new Error(
                    'Guess submission failed.',
                )
            }

            const data: GameState =
                await response.json()

            const savedGame: SavedGame =
                {
                    date: data.date,
                    guess_ids:
                        nextGuessIds,
                }

            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(
                    savedGame,
                ),
            )

            setGuessedIds(
                nextGuessIds,
            )

            setGameState(data)

            /*
             * Automotive Universe progression:
             *
             * At most one car can be unlocked per day, and only
             * by correctly guessing today's target.
             *
             * Wrong guesses do not unlock their own cars.
             * Losing does not unlock the revealed target.
             */
            if (
                data.won &&
                data.target !== null
            ) {
                saveUnlocks([
                    data.target.id,
                ])
            }

            setQuery('')
            setResults([])
        } catch (submitError) {
            console.error(
                submitError,
            )

            setError(
                'Could not submit your guess. Please try again.',
            )
        } finally {
            setIsSubmitting(
                false,
            )
        }
    }


    return (
        <>
            <Header
                onOpenRules={() =>
                    setShowRules(true)
                }
                onOpenGraph={
                    openGraph
                }
                onOpenGame={
                    openGame
                }
                graphView={
                    view === 'graph'
                }
            />

            {view === 'graph' ? (
                <AutomotiveUniverse
                    unlockedVehicleIds={
                        unlockedVehicleIds
                    }
                    newlyUnlockedVehicleId={
                        pendingUniverseUnlockId
                    }
                    onUnlockAnimationComplete={(
                        vehicleId,
                    ) => {
                        clearPendingUniverseUnlockId(
                            vehicleId,
                        )

                        setPendingUniverseUnlockId(
                            (current) =>
                                current === vehicleId
                                    ? null
                                    : current,
                        )
                    }}
                />
            ) : (
                <main>
                    {isLoadingGame ? (
                        <p className="game-loading">
                            Loading
                            today&apos;s
                            Cardle...
                        </p>
                    ) : (
                        <>
                            {error && (
                                <p className="app-error">
                                    {
                                        error
                                    }
                                </p>
                            )}

                            <GuessBoard
                                gameState={
                                    gameState
                                }
                            />

                            {!gameState?.finished && (
                                <VehicleSearch
                                    query={
                                        query
                                    }
                                    results={
                                        results
                                    }
                                    guessedIds={
                                        guessedIds
                                    }
                                    gameFinished={
                                        false
                                    }
                                    isSearching={
                                        isSearching
                                    }
                                    isSubmitting={
                                        isSubmitting
                                    }
                                    onQueryChange={
                                        setQuery
                                    }
                                    onGuess={
                                        submitGuess
                                    }
                                />
                            )}
                        </>
                    )}
                </main>
            )}

            {showRules && (
                <HowToPlay
                    onClose={() =>
                        setShowRules(
                            false,
                        )
                    }
                />
            )}
        </>
    )
}


export default App
