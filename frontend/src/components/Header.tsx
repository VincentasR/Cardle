type HeaderProps = {
    onOpenRules: () => void
    onOpenGraph: () => void
    onOpenGame: () => void
    graphView: boolean
}

function Header({
    onOpenRules,
    onOpenGraph,
    onOpenGame,
    graphView,
}: HeaderProps) {
    return (
        <header
            className={
                graphView
                    ? 'site-header site-header-dark'
                    : 'site-header'
            }
        >
            <button
                className="header-action header-profile"
                aria-label="Profile"
            >
                <span className="profile-icon">
                    ●
                </span>
            </button>

            <button
                className="cardle-logo"
                aria-label="Today's Cardle"
                onClick={onOpenGame}
            >
                CARDLE
            </button>

            <div className="header-right">
                <button
                    className="header-action header-rules"
                    aria-label="How to play"
                    onClick={onOpenRules}
                >
                    ?
                </button>

                <button
                    className="header-action header-graph"
                    aria-label="Automotive universe"
                    aria-current={
                        graphView
                            ? 'page'
                            : undefined
                    }
                    onClick={onOpenGraph}
                >
                    Graph
                </button>
            </div>
        </header>
    )
}

export default Header
