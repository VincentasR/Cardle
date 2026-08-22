from .game_metadata import (
    MANUFACTURER_ORIGINS,
    VEHICLE_CLASS_ORANGE_PAIRS,
    VEHICLE_CLASS_YELLOW_PAIRS,
)
from .models import (
    Closeness,
    ColorFeedback,
    GameVehicle,
    GuessFeedback,
    NamedEntity,
    OrderedFeedback,
)


class VehicleComparer:
    def compare(
        self,
        guess: GameVehicle,
        target: GameVehicle,
    ) -> GuessFeedback:
        return GuessFeedback(
            closeness=self._compare_closeness(
                guess,
                target,
            ),

            manufacturer=self._compare_manufacturer(
                guess,
                target,
            ),

            production_start=self._compare_ordered(
                guess.production_start,
                target.production_start,
            ),

            production_end=self._compare_ordered(
                guess.production_end,
                target.production_end,
            ),

            vehicle_class=self._compare_vehicle_classes(
                guess.vehicle_classes,
                target.vehicle_classes,
            ),

            body_style=self._compare_sets(
                guess.body_styles,
                target.body_styles,
            ),

            engine_family=self._compare_engine_hierarchy(
                guess,
                target,
            ),

            power=self._compare_ordered(
                guess.power_hp,
                target.power_hp,
            ),

            drivetrain=self._compare_sets(
                guess.drivetrains,
                target.drivetrains,
            ),
        )

    @staticmethod
    def _compare_closeness(
        guess: GameVehicle,
        target: GameVehicle,
    ) -> Closeness:
        if guess.id == target.id:
            return Closeness.MATCH

        if guess.variant.id == target.variant.id:
            return Closeness.VERY_CLOSE

        if (
            target.variant.id in guess.lineage_neighbor_ids
            or guess.variant.id in target.lineage_neighbor_ids
        ):
            return Closeness.CLOSE

        if (
            guess.model is not None
            and target.model is not None
            and guess.model.id == target.model.id
        ):
            return Closeness.RELATED

        if guess.manufacturer.id == target.manufacturer.id:
            return Closeness.FAR

        return Closeness.COLD

    @staticmethod
    def _compare_manufacturer(
        guess: GameVehicle,
        target: GameVehicle,
    ) -> ColorFeedback:
        if guess.manufacturer.id == target.manufacturer.id:
            return ColorFeedback.GREEN

        guess_origin = MANUFACTURER_ORIGINS.get(
            guess.manufacturer.id
        )
        target_origin = MANUFACTURER_ORIGINS.get(
            target.manufacturer.id
        )

        if guess_origin is None or target_origin is None:
            return ColorFeedback.UNKNOWN

        if guess_origin.country == target_origin.country:
            return ColorFeedback.YELLOW

        if guess_origin.continent == target_origin.continent:
            return ColorFeedback.ORANGE

        return ColorFeedback.BLACK

    @staticmethod
    def _compare_ordered(
        guess: int | None,
        target: int | None,
    ) -> OrderedFeedback:
        if guess is None or target is None:
            return OrderedFeedback.UNKNOWN

        if guess == target:
            return OrderedFeedback.GREEN

        if target > guess:
            return OrderedFeedback.UP

        return OrderedFeedback.DOWN

    @staticmethod
    def _entity_ids(
        entities: frozenset[NamedEntity],
    ) -> set[str]:
        return {
            entity.id
            for entity in entities
        }

    @classmethod
    def _compare_engine_hierarchy(
        cls,
        guess: GameVehicle,
        target: GameVehicle,
    ) -> ColorFeedback:
        """
        Compare engines by the deepest shared engine hierarchy level.

        GREEN:
            at least one exact Engine is shared

        YELLOW:
            no exact Engine is shared, but at least one EngineFamily is

        ORANGE:
            no exact Engine/Family is shared, but an EngineSeries is

        BLACK:
            both vehicles have engine information, but no level matches

        UNKNOWN:
            either vehicle has no usable engine identity information
        """

        guess_has_engine_info = bool(
            guess.engines
            or guess.engine_families
            or guess.engine_series
        )
        target_has_engine_info = bool(
            target.engines
            or target.engine_families
            or target.engine_series
        )

        if not guess_has_engine_info or not target_has_engine_info:
            return ColorFeedback.UNKNOWN

        if (
            cls._entity_ids(guess.engines)
            & cls._entity_ids(target.engines)
        ):
            return ColorFeedback.GREEN

        if (
            cls._entity_ids(guess.engine_families)
            & cls._entity_ids(target.engine_families)
        ):
            return ColorFeedback.YELLOW

        if (
            cls._entity_ids(guess.engine_series)
            & cls._entity_ids(target.engine_series)
        ):
            return ColorFeedback.ORANGE

        return ColorFeedback.BLACK

    @staticmethod
    def _compare_sets(
        guess: frozenset[NamedEntity],
        target: frozenset[NamedEntity],
    ) -> ColorFeedback:
        if not guess or not target:
            return ColorFeedback.UNKNOWN

        guess_ids = {
            entity.id
            for entity in guess
        }

        target_ids = {
            entity.id
            for entity in target
        }

        if guess_ids == target_ids:
            return ColorFeedback.GREEN

        if guess_ids & target_ids:
            return ColorFeedback.YELLOW

        return ColorFeedback.BLACK

    @staticmethod
    def _compare_vehicle_classes(
        guess: frozenset[NamedEntity],
        target: frozenset[NamedEntity],
    ) -> ColorFeedback:
        if not guess or not target:
            return ColorFeedback.UNKNOWN

        guess_ids = {
            entity.id
            for entity in guess
        }

        target_ids = {
            entity.id
            for entity in target
        }

        if guess_ids & target_ids:
            return ColorFeedback.GREEN

        guess_names = {
            entity.name
            for entity in guess
        }

        target_names = {
            entity.name
            for entity in target
        }

        for guess_name in guess_names:
            for target_name in target_names:
                pair = frozenset({
                    guess_name,
                    target_name,
                })

                if pair in VEHICLE_CLASS_YELLOW_PAIRS:
                    return ColorFeedback.YELLOW

        for guess_name in guess_names:
            for target_name in target_names:
                pair = frozenset({
                    guess_name,
                    target_name,
                })

                if pair in VEHICLE_CLASS_ORANGE_PAIRS:
                    return ColorFeedback.ORANGE

        return ColorFeedback.BLACK