"""A training session: a participant plus an ordered set of observations."""

import statistics

from analysis import compute_summary_statistics, detect_recovery, explain_classification
from observation import Observation
from participant import Participant


class Session:
    """Groups one :class:`Participant` with many :class:`Observation` windows.

    This is the assignment's clearest example of composition: a Session
    *has a* Participant and *has* Observations. It does not inherit from
    either — a session is not a kind of participant or a kind of
    observation — so composition is the right relationship here, not
    inheritance.
    """

    #: Below this many usable observations, a session cannot be classified.
    MINIMUM_USABLE_OBSERVATIONS = 3

    def __init__(self, participant, observations):
        self._participant = participant
        self._observations = list(observations)

    @classmethod
    def from_raw(cls, profile, raw_observations):
        """Alternate constructor: build a Session straight from generator output."""
        participant = Participant.from_profile(profile)
        observations = [Observation.from_dict(raw) for raw in raw_observations]
        return cls(participant, observations)

    @property
    def participant(self):
        return self._participant

    @property
    def observations(self):
        return list(self._observations)

    @property
    def usable_observations(self):
        """Observations that are both valid and reliable enough to analyze."""
        return [observation for observation in self._observations if observation.is_reliable]

    @staticmethod
    def classification_thresholds():
        """The intensity-band thresholds used by :meth:`classify`.

        A static method rather than an instance method: the thresholds are a
        fixed domain constant that does not depend on any particular
        session's data, but they belong conceptually with Session rather
        than floating in module scope.
        """
        return {
            "resting": {"max_hr_delta": 12, "max_activity": 0.25},
            "moderate activity": {"max_hr_delta": 45, "max_activity": 0.60},
            # anything above the "moderate activity" band is "high activity"
        }

    def _average_delta(self, field, baseline_fn):
        usable = self.usable_observations
        if not usable:
            return None
        return round(
            statistics.fmean(baseline_fn(observation[field]) for observation in usable), 2
        )

    def average_heart_rate_delta(self):
        return self._average_delta("heart_rate", self._participant.heart_rate_delta)

    def average_skin_response_delta(self):
        return self._average_delta("skin_response", self._participant.skin_response_delta)

    def average_temperature_delta(self):
        return self._average_delta("temperature", self._participant.temperature_delta)

    def average_activity_level(self):
        usable = self.usable_observations
        if not usable:
            return None
        return statistics.fmean(observation["activity_level"] for observation in usable)

    def summarize(self, field):
        """Average/min/max/count for one field, over usable observations only."""
        return compute_summary_statistics(
            observation[field] for observation in self.usable_observations
        )

    def is_recovering(self):
        return detect_recovery(self.usable_observations, self._participant)

    def classify(self):
        """Classify this session as resting / moderate / high activity / recovering / insufficient data."""
        usable = self.usable_observations
        if len(usable) < self.MINIMUM_USABLE_OBSERVATIONS:
            return "insufficient data"

        if self.is_recovering():
            return "recovering"

        hr_delta = self.average_heart_rate_delta()
        activity = self.average_activity_level()
        thresholds = self.classification_thresholds()

        resting = thresholds["resting"]
        if hr_delta <= resting["max_hr_delta"] and activity <= resting["max_activity"]:
            return "resting"

        moderate = thresholds["moderate activity"]
        if hr_delta <= moderate["max_hr_delta"] and activity <= moderate["max_activity"]:
            return "moderate activity"

        return "high activity"

    def build_report(self):
        """Return a structured ``dict`` describing this session (required deliverable)."""
        usable = self.usable_observations
        total = len(self._observations)

        report = {
            "participant_id": self._participant.participant_id,
            "total_observations": total,
            "usable_observations": len(usable),
            "rejected_observations": total - len(usable),
            "classification": self.classify(),
            "average_heart_rate_delta": self.average_heart_rate_delta(),
            "average_skin_response_delta": self.average_skin_response_delta(),
            "average_temperature_delta": self.average_temperature_delta(),
            "is_recovering": self.is_recovering() if usable else False,
            "heart_rate": self.summarize("heart_rate"),
            "activity_level": self.summarize("activity_level"),
            "skin_response": self.summarize("skin_response"),
            "temperature": self.summarize("temperature"),
        }
        report["explanation"] = explain_classification(report)
        return report

    def __repr__(self):
        return (
            f"Session(participant={self._participant.participant_id!r}, "
            f"observations={len(self._observations)})"
        )
