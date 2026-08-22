type HeaderProps = {
    onOpenRules: () => void
}

function Header({ onOpenRules }: HeaderProps) {
    return (
        <header className="site-header">
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
                >
                    Graph
                </button>
            </div>
        </header>
    )
}

export default Header