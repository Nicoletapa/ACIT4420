"""A single observation window within a fitness session."""

from measurements import Measurement


class Observation:
    """One measurement window (one dictionary from the data generator).

    An Observation is *composed of* several :class:`~measurements.Measurement`
    objects, one per required field, rather than storing raw numbers
    directly. That keeps per-field validation rules where they belong (on
    the Measurement subclasses) and lets Observation focus on combining
    them: is this window valid, is it reliable, what went wrong with it.
    """

    #: Fields every observation dictionary is expected to provide.
    REQUIRED_FIELDS = (
        "heart_rate",
        "skin_response",
        "temperature",
        "activity_level",
        "signal_quality",
    )

    #: A window is only "reliable" (trusted for analysis) above this signal quality.
    RELIABLE_SIGNAL_QUALITY = 0.60

    def __init__(self, timestamp, measurements):
        self._timestamp = timestamp
        self._measurements = measurements  # dict[str, Measurement]

    @classmethod
    def from_dict(cls, raw_observation):
        """Alternate constructor: build an Observation from a raw generator dict.

        Missing keys are treated the same as an explicit ``None`` value, so a
        dictionary that is missing a field entirely is flagged rather than
        raising a ``KeyError``.
        """
        timestamp = raw_observation.get("timestamp")
        measurements = {
            field: Measurement.create(field, raw_observation.get(field))
            for field in cls.REQUIRED_FIELDS
        }
        return cls(timestamp, measurements)

    @property
    def timestamp(self):
        return self._timestamp

    def __getitem__(self, field):
        """Convenience accessor: ``observation["heart_rate"]`` -> raw value."""
        return self._measurements[field].value

    @property
    def is_valid(self):
        """True when every required field is present and physically plausible."""
        return all(measurement.is_valid for measurement in self._measurements.values())

    @property
    def is_reliable(self):
        """Valid *and* the sensor itself reported acceptable signal quality.

        This is the flag used to decide whether an observation counts as
        "usable" for the session's analysis.
        """
        if not self.is_valid:
            return False
        return self["signal_quality"] >= self.RELIABLE_SIGNAL_QUALITY

    @property
    def issues(self):
        """Dict of ``{field: issue}`` for every field that failed validation."""
        return {
            field: measurement.issue
            for field, measurement in self._measurements.items()
            if measurement.issue
        }

    def __repr__(self):
        return f"Observation(timestamp={self._timestamp!r}, valid={self.is_valid})"
