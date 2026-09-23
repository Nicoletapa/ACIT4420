"""Builds the minimum-required demonstration scenarios for Option A.

Calls the instructor-supplied :mod:`data_generator` module to obtain raw
profile and observation dictionaries, then packages them with a display
title for :mod:`main` and :mod:`tests`. This module does not perform any
analysis itself -- it only arranges instructor-supplied data.
"""

from data_generator import generate_fitness_data

# (scenario key, generator scenario name, seed, number_of_windows, display title)
# The five entries below are the assignment's five required minimum scenarios.
SCENARIO_DEFINITIONS = [
    ("resting", "resting", 1, 12, "Resting session"),
    ("moderate_activity", "moderate_activity", 2, 12, "Moderate activity session"),
    ("high_activity", "high_activity", 3, 12, "High activity session"),
    ("recovery", "recovery", 4, 14, "Activity followed by recovery"),
    ("poor_quality", "poor_quality", 5, 12, "Poor-quality / invalid sensor data"),
]


def build_sample_sessions(participant_id="P001"):
    """Return ``[(title, profile, raw_observations), ...]`` for every minimum scenario."""
    samples = []
    for key, scenario, seed, windows, title in SCENARIO_DEFINITIONS:
        profile, observations = generate_fitness_data(
            participant_id=f"{participant_id}-{key}",
            scenario=scenario,
            seed=seed,
            number_of_windows=windows,
        )
        samples.append((title, profile, observations))
    return samples
