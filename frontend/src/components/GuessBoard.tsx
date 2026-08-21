import type { GameState } from '../types/game'

import GuessRow from './GuessRow'


type GuessBoardProps = {
    gameState: GameState | null
}


function GuessBoard({
    gameState,
}: GuessBoardProps) {
    const guessCount =
        gameState?.guess_count ?? 0

    const maxGuesses =
        gameState?.max_guesses ?? 7

    return (
        <section className="guess-board">
            <div className="guess-progress">
                {gameState?.won && (
                    <span>
                        Solved in {guessCount} guesses
                    </span>
                )}

                {gameState?.lost && (
                    <span>
                        Out of guesses
                    </span>
                )}

                {!gameState?.finished && (
                    <span>
                        Guess {guessCount + 1} / {maxGuesses}
                    </span>
                )}
            </div>

            <div className="guess-list">
                {gameState?.guesses.map((result) => (
                    <GuessRow
                        key={result.guess_number}
                        result={result}
                    />
                ))}
            </div>

            {gameState?.finished && gameState.target && (
                <div className="game-result">
                    <p>
                        {gameState.won
                            ? 'Correct!'
                            : 'The hidden car was:'}
                    </p>

                    <strong>
                        {gameState.target.display_name}
                    </strong>
                </div>
            )}
        </section>
    )
}


export default GuessBoard