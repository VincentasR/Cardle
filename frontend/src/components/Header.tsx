function Header() {
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

            <button
                className="header-action header-graph"
                aria-label="Automotive universe"
            >
                Graph
            </button>
        </header>
    )
}


export default Header