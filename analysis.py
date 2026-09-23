"""Standalone calculation, validation and presentation functions.

These functions are deliberately kept free of any class state: they take plain
values in and return plain values out, so they can be reused by any class
(or by :mod:`tests`) without needing an object to call them on.
"""

import statistics


def is_plausible(value, low, high):
    """Validation: True if ``value`` is a real number inside ``[low, high]``.

    ``None`` and booleans (``True``/``False`` are technically ``int`` in
    Python) are always rejected, since a missing or boolean reading is never
    a plausible sensor value.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return low <= value <= high


def compute_summary_statistics(values):
    """Calculation: average/minimum/maximum/count for a list of numbers.

    Returns ``None`` when ``values`` is empty, so callers can distinguish
    "no usable data" from a genuine zero-valued summary.
    """
    values = list(values)
    if not values:
        return None
    return {
        "average": round(statistics.fmean(values), 3),
        "minimum": round(min(values), 3),
        "maximum": round(max(values), 3),
        "count": len(values),
    }


def detect_recovery(observations, participant, tail_fraction=0.3,
                     decline_ratio=0.5, elevated_threshold=15):
    """Calculation: does the session show recovery near the end?

    ``observations`` should already be filtered to usable observations. The
    session counts as "recovering" when the early portion is clearly
    elevated above the participant's baseline and the late portion has
    dropped back down to roughly half (or less) of that elevation, for both
    heart rate and activity level.
    """
    ordered = sorted(observations, key=lambda observation: observation.timestamp)
    total = len(ordered)
    if total < 4:
        return False

    window = max(2, round(total * tail_fraction))
    head, tail = ordered[:window], ordered[-window:]

    head_hr_delta = statistics.fmean(
        participant.heart_rate_delta(observation["heart_rate"]) for observation in head
    )
    tail_hr_delta = statistics.fmean(
        participant.heart_rate_delta(observation["heart_rate"]) for observation in tail
    )
    head_activity = statistics.fmean(observation["activity_level"] for observation in head)
    tail_activity = statistics.fmean(observation["activity_level"] for observation in tail)

    was_elevated = head_hr_delta >= elevated_threshold or head_activity >= 0.35
    heart_rate_declined = tail_hr_delta <= head_hr_delta * decline_ratio
    activity_declined = tail_activity <= head_activity * decline_ratio + 0.05

    return was_elevated and heart_rate_declined and activity_declined


def explain_classification(report):
    """Presentation: turn a session report dict into a one-paragraph explanation."""
    classification = report["classification"]
    usable = report["usable_observations"]
    total = report["total_observations"]

    if classification == "insufficient data":
        return (
            f"Only {usable} of {total} observations were usable (valid and "
            "reliable enough to trust), which is below the minimum needed "
            "to classify this session."
        )

    hr_delta = report["average_heart_rate_delta"]
    activity_stats = report["activity_level"]
    activity = activity_stats["average"] if activity_stats else 0.0

    base = (
        f"Based on {usable} of {total} usable observations, heart rate "
        f"averaged {hr_delta:+.1f} bpm relative to the participant's "
        f"baseline and activity level averaged {activity:.2f}."
    )

    tail = {
        "recovering": (
            " Heart rate and activity level both declined substantially in "
            "the final part of the session, which is characteristic of "
            "recovery after activity."
        ),
        "resting": (
            " Both values stayed close to the participant's resting "
            "baseline throughout the session."
        ),
        "moderate activity": (
            " Values were moderately elevated above baseline throughout "
            "the session, consistent with moderate-intensity exercise."
        ),
        "high activity": (
            " Values were substantially elevated above baseline throughout "
            "the session, consistent with high-intensity exercise."
        ),
    }.get(classification, "")

    return base + tail


def format_console_report(report):
    """Presentation: render a session report dict as readable console text."""
    lines = [
        f"Participant: {report['participant_id']}",
        f"Classification: {report['classification'].upper()}",
        (
            f"Observations: {report['usable_observations']} usable / "
            f"{report['total_observations']} total "
            f"({report['rejected_observations']} rejected or flagged as unreliable)"
        ),
    ]

    for field in ("heart_rate", "activity_level", "skin_response", "temperature"):
        stats = report.get(field)
        if stats:
            lines.append(
                f"  {field:>14}: avg={stats['average']:.2f}  "
                f"min={stats['minimum']:.2f}  max={stats['maximum']:.2f}  (n={stats['count']})"
            )

    lines.append(f"Explanation: {report['explanation']}")
    return "\n".join(lines)
