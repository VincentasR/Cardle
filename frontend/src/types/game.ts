export type VehicleSearchResult = {
    id: string
    display_name: string
}


export type GuessVehicle = {
    id: string
    display_name: string
    manufacturer: string

    production_start: number | null
    production_end: number | null

    vehicle_classes: string[]
    body_styles: string[]

    engine_series: string[]
    engine_families: string[]
    engines: string[]

    power_hp: number | null

    drivetrains: string[]
}


export type GuessFeedback = {
    closeness: string

    manufacturer: string

    production_start: string
    production_end: string

    vehicle_class: string
    body_style: string
    engine_family: string

    power: string

    drivetrain: string
}


export type GuessResult = {
    guess_number: number

    vehicle: GuessVehicle
    feedback: GuessFeedback
}


export type GameState = {
    date: string

    won: boolean
    lost: boolean
    finished: boolean

    guess_count: number
    max_guesses: number
    remaining_guesses: number

    target: GuessVehicle | null

    guesses: GuessResult[]
}


export type SavedGame = {
    date: string
    guess_ids: string[]
}