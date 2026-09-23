"""The participant being monitored and their personal reference measurements."""


class Participant:
    """A participant and the personal baseline their session is compared against.

    ``participant_id`` is stored behind a protected attribute and exposed
    only through a read-only property, with validation applied at
    construction time (the assignment's "private/protected attribute
    controlled through a property" requirement).
    """

    def __init__(self, participant_id, baseline_heart_rate,
                 baseline_skin_response, baseline_temperature):
        self._participant_id = self._validated_id(participant_id)
        self._baseline_heart_rate = baseline_heart_rate
        self._baseline_skin_response = baseline_skin_response
        self._baseline_temperature = baseline_temperature

    @staticmethod
    def _validated_id(participant_id):
        if not isinstance(participant_id, str) or not participant_id.strip():
            raise ValueError("participant_id must be a non-empty string")
        return participant_id

    @classmethod
    def from_profile(cls, profile):
        """Alternate constructor: build a Participant from the generator's profile dict."""
        return cls(
            participant_id=profile["participant_id"],
            baseline_heart_rate=profile["baseline_heart_rate"],
            baseline_skin_response=profile["baseline_skin_response"],
            baseline_temperature=profile["baseline_temperature"],
        )

    @property
    def participant_id(self):
        return self._participant_id

    @property
    def baseline_heart_rate(self):
        return self._baseline_heart_rate

    @property
    def baseline_skin_response(self):
        return self._baseline_skin_response

    @property
    def baseline_temperature(self):
        return self._baseline_temperature

    def heart_rate_delta(self, heart_rate):
        """How far a measured heart rate sits above (or below) this participant's baseline."""
        return heart_rate - self._baseline_heart_rate

    def skin_response_delta(self, skin_response):
        return skin_response - self._baseline_skin_response

    def temperature_delta(self, temperature):
        return temperature - self._baseline_temperature

    def __repr__(self):
        return f"Participant({self._participant_id!r})"
