import type { GuessResult, GuessVehicle } from '../types/game'


type GuessRowProps = {
    result: GuessResult
}


function displayList(values: string[]) {
    if (values.length === 0) {
        return 'Unknown'
    }

    return values.join(', ')
}

function displayEngine(vehicle: GuessVehicle): string {
    if (vehicle.engines.length > 0) {
        return vehicle.engines.join(', ')
    }

    if (vehicle.engine_families.length > 0) {
        return vehicle.engine_families.join(', ')
    }

    if (vehicle.engine_series.length > 0) {
        return vehicle.engine_series.join(', ')
    }

    return 'Unknown'
}



function orderedArrow(feedback: string) {
    if (feedback === 'up') {
        return ' ↑'
    }

    if (feedback === 'down') {
        return ' ↓'
    }

    return ''
}

function productionFeedbackClass(
    productionStart: string,
    productionEnd: string,
): string {
    const matchingYears = [
        productionStart,
        productionEnd,
    ].filter((feedback) => feedback === 'green').length

    if (matchingYears === 2) {
        return 'feedback-green'
    }

    if (matchingYears === 1) {
        return 'feedback-yellow'
    }

    return 'ordered-production'
}

function closenessLabel(closeness: string) {
    return closeness
        .replace('_', ' ')
        .toUpperCase()
}

function closenessLevel(
    closeness: string,
) {
    switch (closeness) {
        case 'far':
            return 1

        case 'related':
            return 2

        case 'close':
            return 3

        case 'very_close':
            return 4

        case 'match':
            return 5

        case 'cold':
        default:
            return 0
    }
}

function ClosenessIndicator({
    closeness,
}: {
    closeness: string
}) {
    const level =
        closenessLevel(closeness)

    return (
        <div className="closeness">
            <div className="closeness-dots">
                {[1, 2, 3, 4, 5].map((dot) => (
                    <span
                        key={dot}
                        className={
                            dot <= level
                                ? 'closeness-dot closeness-dot-filled'
                                : 'closeness-dot'
                        }
                    />
                ))}
            </div>

            <span className="closeness-label">
                {closenessLabel(closeness)}
            </span>
        </div>
    )
}

function GuessRow({
    result,
}: GuessRowProps) {
    const vehicle = result.vehicle
    const feedback = result.feedback

    return (
        <article className="guess-row">
            <div className="guess-header">
                <h3 className="guess-name">
                    {vehicle.display_name}
                </h3>

                <ClosenessIndicator
                    closeness={feedback.closeness}
                />
            </div>

            <div className="property-grid">
                <div
                    className={`property-cell feedback-${feedback.manufacturer}`}
                >
                    <span className="property-value">
                        {vehicle.manufacturer}
                    </span>

                    <span className="property-label">
                        Manufacturer
                    </span>
                </div>


                <div
                    className={`property-cell ${productionFeedbackClass(
                        feedback.production_start,
                        feedback.production_end,
                    )}`}
                >
                    <span className="property-value">
                        {vehicle.production_start ?? 'Unknown'}
                        {orderedArrow(feedback.production_start)}

                        {'–'}

                        {vehicle.production_end ?? 'Unknown'}
                        {orderedArrow(feedback.production_end)}
                    </span>
                        
                    <span className="property-label">
                        Production
                    </span>
                </div>


                <div
                    className={`property-cell feedback-${feedback.vehicle_class}`}
                >
                    <span className="property-value">
                        {displayList(
                            vehicle.vehicle_classes,
                        )}
                    </span>

                    <span className="property-label">
                        Class
                    </span>
                </div>


                <div
                    className={`property-cell feedback-${feedback.body_style}`}
                >
                    <span className="property-value">
                        {displayList(
                            vehicle.body_styles,
                        )}
                    </span>

                    <span className="property-label">
                        Body style
                    </span>
                </div>


                <div
                    className={`property-cell feedback-${feedback.engine_family}`}
                >
                    <span className="property-value">
                        {displayEngine(
                            vehicle
                        )}
                    </span>

                    <span className="property-label">
                        Engine
                    </span>
                </div>


                <div
                    className={`property-cell ordered-${feedback.power}`}
                >
                    <span className="property-value">
                        {vehicle.power_hp ?? 'Unknown'}

                        {vehicle.power_hp !== null && ' hp'}

                        {orderedArrow(
                            feedback.power,
                        )}
                    </span>

                    <span className="property-label">
                        Power
                    </span>
                </div>


                <div
                    className={`property-cell feedback-${feedback.drivetrain}`}
                >
                    <span className="property-value">
                        {displayList(
                            vehicle.drivetrains,
                        )}
                    </span>

                    <span className="property-label">
                        Drivetrain
                    </span>
                </div>
            </div>
        </article>
    )
}


export default GuessRow