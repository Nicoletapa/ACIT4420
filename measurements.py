"""Per-field measurement classes.

Each physiological field reported by the sensors (heart rate, skin response,
temperature, activity level, signal quality) gets its own small class that
knows the physically plausible range for *that* field and how to decide
whether a raw value is usable. :class:`Measurement` holds the shared logic;
the subclasses override what differs.
"""

from analysis import is_plausible


class Measurement:
    """Base class for a single reading within an observation window.

    Subclasses override :attr:`PLAUSIBLE_RANGE` (and, where a field needs an
    extra domain rule, :meth:`_evaluate`) to specialise validation for their
    field. Client code should not need to know which subclass it is holding;
    it only relies on the interface defined here (``value``, ``is_valid``,
    ``issue``).
    """

    #: Overridden by subclasses: the physically plausible ``(low, high)`` range.
    PLAUSIBLE_RANGE = (float("-inf"), float("inf"))

    #: Maps a raw-dictionary field name to the Measurement subclass that
    #: understands it. Populated once, after every subclass is defined below.
    _REGISTRY = {}

    def __init__(self, raw_value):
        self._raw_value = raw_value
        self._issue = self._evaluate(raw_value)

    def _evaluate(self, raw_value):
        """Return a short issue string, or ``None`` if the value is usable."""
        if raw_value is None:
            return "missing"
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            return "non-numeric"
        low, high = self.PLAUSIBLE_RANGE
        if not is_plausible(raw_value, low, high):
            return "out-of-range"
        return None

    @property
    def value(self):
        """The raw value. Still returned when flagged, so issues can be logged."""
        return self._raw_value

    @property
    def is_valid(self):
        return self._issue is None

    @property
    def issue(self):
        return self._issue

    @classmethod
    def create(cls, field_name, raw_value):
        """Factory: build the Measurement subclass registered for ``field_name``.

        A classmethod is the natural fit here: the caller (``Observation``)
        just wants "the right kind of Measurement for this field" without
        needing to import or name every subclass itself.
        """
        measurement_cls = cls._REGISTRY.get(field_name, Measurement)
        return measurement_cls(raw_value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._raw_value!r})"


class HeartRateMeasurement(Measurement):
    """Heart rate in beats per minute."""

    PLAUSIBLE_RANGE = (30, 220)

    def _evaluate(self, raw_value):
        # Reuse the base checks first, then add a field-specific rule: a
        # wearable reports whole beats per minute, so a fractional value
        # signals a corrupted reading even if it falls in-range.
        issue = super()._evaluate(raw_value)
        if issue is None and isinstance(raw_value, float) and not raw_value.is_integer():
            return "non-integer-heart-rate"
        return issue


class SkinResponseMeasurement(Measurement):
    """Simulated galvanic skin response, in sensor units (never negative)."""

    PLAUSIBLE_RANGE = (0.0, 50.0)


class TemperatureMeasurement(Measurement):
    """Skin temperature in degrees Celsius."""

    PLAUSIBLE_RANGE = (20.0, 45.0)


class ActivityLevelMeasurement(Measurement):
    """Normalized movement level, 0 (still) to 1 (maximal)."""

    PLAUSIBLE_RANGE = (0.0, 1.0)


class SignalQualityMeasurement(Measurement):
    """Sensor-reported measurement reliability, 0 (unreliable) to 1 (clean)."""

    PLAUSIBLE_RANGE = (0.0, 1.0)


Measurement._REGISTRY = {
    "heart_rate": HeartRateMeasurement,
    "skin_response": SkinResponseMeasurement,
    "temperature": TemperatureMeasurement,
    "activity_level": ActivityLevelMeasurement,
    "signal_quality": SignalQualityMeasurement,
}
