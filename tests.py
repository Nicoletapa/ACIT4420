"""Unit tests for the Smart Fitness Session Analyzer.

Uses only ``unittest`` from the Python standard library (per the
assignment's permitted-tools list). Run with:

    python3 -m unittest tests.py -v

or simply:

    python3 tests.py
"""

import unittest

from analysis import compute_summary_statistics, detect_recovery, is_plausible
from data_generator import generate_fitness_data
from measurements import HeartRateMeasurement, Measurement, SignalQualityMeasurement
from observation import Observation
from participant import Participant
from session import Session


class IsPlausibleTests(unittest.TestCase):
    def test_accepts_value_in_range(self):
        self.assertTrue(is_plausible(50, 0, 100))

    def test_rejects_value_out_of_range(self):
        self.assertFalse(is_plausible(150, 0, 100))

    def test_rejects_none(self):
        self.assertFalse(is_plausible(None, 0, 100))

    def test_rejects_boolean(self):
        # bool is technically an int subclass in Python; must not slip through.
        self.assertFalse(is_plausible(True, 0, 100))

    def test_rejects_non_numeric(self):
        self.assertFalse(is_plausible("50", 0, 100))


class ComputeSummaryStatisticsTests(unittest.TestCase):
    def test_typical_values(self):
        stats = compute_summary_statistics([1, 2, 3, 4])
        self.assertEqual(stats["average"], 2.5)
        self.assertEqual(stats["minimum"], 1)
        self.assertEqual(stats["maximum"], 4)
        self.assertEqual(stats["count"], 4)

    def test_empty_list_returns_none(self):
        self.assertIsNone(compute_summary_statistics([]))


class MeasurementTests(unittest.TestCase):
    def test_valid_heart_rate(self):
        measurement = HeartRateMeasurement(72)
        self.assertTrue(measurement.is_valid)
        self.assertIsNone(measurement.issue)

    def test_missing_value_is_flagged(self):
        measurement = HeartRateMeasurement(None)
        self.assertFalse(measurement.is_valid)
        self.assertEqual(measurement.issue, "missing")

    def test_impossible_value_is_flagged(self):
        measurement = HeartRateMeasurement(265)
        self.assertFalse(measurement.is_valid)
        self.assertEqual(measurement.issue, "out-of-range")

    def test_non_integer_heart_rate_is_flagged(self):
        # HeartRateMeasurement overrides _evaluate to add this extra rule.
        measurement = HeartRateMeasurement(72.5)
        self.assertFalse(measurement.is_valid)
        self.assertEqual(measurement.issue, "non-integer-heart-rate")

    def test_factory_builds_the_right_subclass(self):
        measurement = Measurement.create("signal_quality", 0.9)
        self.assertIsInstance(measurement, SignalQualityMeasurement)

    def test_factory_unknown_field_falls_back_to_base(self):
        measurement = Measurement.create("unknown_field", 1)
        self.assertIsInstance(measurement, Measurement)


class ObservationTests(unittest.TestCase):
    def _raw(self, **overrides):
        base = {
            "timestamp": 0,
            "heart_rate": 100,
            "skin_response": 1.5,
            "temperature": 32.0,
            "activity_level": 0.5,
            "signal_quality": 0.9,
        }
        base.update(overrides)
        return base

    def test_valid_and_reliable_observation(self):
        observation = Observation.from_dict(self._raw())
        self.assertTrue(observation.is_valid)
        self.assertTrue(observation.is_reliable)
        self.assertEqual(observation.issues, {})

    def test_missing_field_makes_observation_invalid(self):
        raw = self._raw()
        del raw["heart_rate"]
        observation = Observation.from_dict(raw)
        self.assertFalse(observation.is_valid)
        self.assertIn("heart_rate", observation.issues)

    def test_low_signal_quality_is_not_reliable_even_if_valid(self):
        observation = Observation.from_dict(self._raw(signal_quality=0.2))
        self.assertTrue(observation.is_valid)
        self.assertFalse(observation.is_reliable)

    def test_getitem_returns_raw_value(self):
        observation = Observation.from_dict(self._raw(heart_rate=88))
        self.assertEqual(observation["heart_rate"], 88)


class ParticipantTests(unittest.TestCase):
    def test_rejects_empty_participant_id(self):
        with self.assertRaises(ValueError):
            Participant(participant_id="  ", baseline_heart_rate=70,
                        baseline_skin_response=1.5, baseline_temperature=32.5)

    def test_heart_rate_delta(self):
        participant = Participant(participant_id="P1", baseline_heart_rate=70,
                                   baseline_skin_response=1.5, baseline_temperature=32.5)
        self.assertEqual(participant.heart_rate_delta(100), 30)

    def test_from_profile(self):
        profile = {
            "participant_id": "P1",
            "baseline_heart_rate": 65,
            "baseline_skin_response": 1.8,
            "baseline_temperature": 32.1,
        }
        participant = Participant.from_profile(profile)
        self.assertEqual(participant.participant_id, "P1")
        self.assertEqual(participant.baseline_heart_rate, 65)


class DetectRecoveryTests(unittest.TestCase):
    def test_flat_high_activity_is_not_recovery(self):
        profile, raw = generate_fitness_data(
            participant_id="X", scenario="high_activity", seed=7, number_of_windows=12)
        session = Session.from_raw(profile, raw)
        self.assertFalse(detect_recovery(session.usable_observations, session.participant))

    def test_declining_session_is_recovery(self):
        profile, raw = generate_fitness_data(
            participant_id="X", scenario="recovery", seed=7, number_of_windows=14)
        session = Session.from_raw(profile, raw)
        self.assertTrue(detect_recovery(session.usable_observations, session.participant))


class SessionClassificationTests(unittest.TestCase):
    """One deterministic seed per required minimum scenario."""

    def _classify(self, scenario, seed, windows=12):
        profile, raw = generate_fitness_data(
            participant_id="X", scenario=scenario, seed=seed, number_of_windows=windows)
        return Session.from_raw(profile, raw).classify()

    def test_resting(self):
        self.assertEqual(self._classify("resting", seed=1), "resting")

    def test_moderate_activity(self):
        self.assertEqual(self._classify("moderate_activity", seed=2), "moderate activity")

    def test_high_activity(self):
        self.assertEqual(self._classify("high_activity", seed=3), "high activity")

    def test_recovery(self):
        self.assertEqual(self._classify("recovery", seed=4, windows=14), "recovering")

    def test_poor_quality(self):
        self.assertEqual(self._classify("poor_quality", seed=5), "insufficient data")

    def test_empty_session_is_insufficient_data(self):
        profile = {
            "participant_id": "X",
            "baseline_heart_rate": 70,
            "baseline_skin_response": 1.5,
            "baseline_temperature": 32.5,
        }
        session = Session.from_raw(profile, [])
        self.assertEqual(session.classify(), "insufficient data")


class SessionReportTests(unittest.TestCase):
    def test_report_is_a_structured_dict_with_expected_keys(self):
        profile, raw = generate_fitness_data(
            participant_id="X", scenario="moderate_activity", seed=2, number_of_windows=12)
        report = Session.from_raw(profile, raw).build_report()

        expected_keys = {
            "participant_id", "total_observations", "usable_observations",
            "rejected_observations", "classification", "average_heart_rate_delta",
            "average_skin_response_delta", "average_temperature_delta",
            "is_recovering", "heart_rate", "activity_level", "skin_response",
            "temperature", "explanation",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["total_observations"], 12)
        self.assertIsInstance(report["explanation"], str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
