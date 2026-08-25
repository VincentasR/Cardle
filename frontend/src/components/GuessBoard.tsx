import type {
    GameState,
    GuessResult,
    GuessVehicle,
} from '../types/game'

import GuessRow from './GuessRow'


type GuessBoardProps = {
    gameState: GameState | null
}


function createAnswerResult(
    vehicle: GuessVehicle,
): GuessResult {
    return {
        guess_number: 0,

        vehicle,

        feedback: {
            closeness: 'match',

            manufacturer: 'green',

            production_start: 'green',
            production_end: 'green',

            vehicle_class: 'green',
            body_style: 'green',
            engine_family: 'green',

            power: 'green',

            drivetrain: 'green',
        },
    }
}


function GuessBoard({
    gameState,
}: GuessBoardProps) {
    const guessCount =
        gameState?.guess_count ?? 0

    const maxGuesses =
        gameState?.max_guesses ?? 7

    const answerResult =
        gameState?.lost &&
        gameState.target !== null
            ? createAnswerResult(
                gameState.target,
            )
            : null

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

            {gameState?.won && (
                <div className="game-result">
                    <p>
                        Correct!
                    </p>
                </div>
            )}

            {answerResult && (
                <div className="game-result">
                    <p>
                        The hidden car was:
                    </p>

                    <GuessRow
                        result={answerResult}
                    />
                </div>
            )}
        </section>
    )
}


export default GuessBoard