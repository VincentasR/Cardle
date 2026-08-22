import { useEffect } from 'react'

type HowToPlayProps = {
    onClose: () => void
}

function HowToPlay({ onClose }: HowToPlayProps) {
    useEffect(() => {
        function handleKeyDown(event: KeyboardEvent) {
            if (event.key === 'Escape') {
                onClose()
            }
        }

        window.addEventListener('keydown', handleKeyDown)

        return () => {
            window.removeEventListener('keydown', handleKeyDown)
        }
    }, [onClose])

    return (
        <div
            className="rules-backdrop"
            onClick={onClose}
        >
            <div
                className="rules-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="rules-title"
                onClick={(event) => event.stopPropagation()}
            >
                <div className="rules-header">
                    <h2 id="rules-title">HOW TO PLAY</h2>

                    <button
                        className="rules-close"
                        type="button"
                        onClick={onClose}
                        aria-label="Close rules"
                    >
                        ×
                    </button>
                </div>

                <div className="rules-content">
                    <p>
                        Guess the hidden car in 7 attempts.
                    </p>

                    <p>
                        Each guess reveals clues about the hidden car.
                    </p>

                    <section>
                        <h3>MATCHES</h3>

                        <div className="rule-color">
                            <span className="rule-swatch feedback-green" />
                            <span><strong>Green</strong> — Exact match</span>
                        </div>

                        <div className="rule-color">
                            <span className="rule-swatch feedback-yellow" />
                            <span><strong>Yellow</strong> — Partial or close match</span>
                        </div>

                        <div className="rule-color">
                            <span className="rule-swatch feedback-orange" />
                            <span><strong>Orange</strong> — Broader related match</span>
                        </div>

                        <div className="rule-color">
                            <span className="rule-swatch feedback-black" />
                            <span><strong>Black</strong> — No match</span>
                        </div>
                    </section>

                    <section>
                        <h3>↑ / ↓</h3>

                        <p>
                            For Production and Power, arrows show whether
                            the hidden car&apos;s value is higher or lower.
                        </p>
                    </section>

                    <section>
                        <h3>ENGINE</h3>

                        <div className="rule-color">
                            <span className="rule-swatch feedback-green" />
                            <span><strong>Green</strong> — Same exact engine</span>
                        </div>

                        <div className="rule-color">
                            <span className="rule-swatch feedback-yellow" />
                            <span><strong>Yellow</strong> — Same engine family</span>
                        </div>

                        <div className="rule-color">
                            <span className="rule-swatch feedback-orange" />
                            <span><strong>Orange</strong> — Same engine series</span>
                        </div>
                    </section>

                    <section>
                        <h3>CLOSENESS</h3>

                        <p>
                            The dots next to each guessed car show how
                            closely the cars themselves are related.
                        </p>

                        <p>
                            More filled dots = closer to the hidden car.
                        </p>
                    </section>
                </div>

                <button
                    className="rules-confirm"
                    type="button"
                    onClick={onClose}
                >
                    Got it
                </button>
            </div>
        </div>
    )
}

export default HowToPlay