"""Entry point for the Smart Fitness Session Analyzer (Option A).

Run with:
    python3 main.py

This prints a readable console report for each of the five minimum-required
scenarios (resting, moderate activity, high activity, activity followed by
recovery, and poor-quality/invalid sensor data), built from the
instructor-supplied data generator.
"""

from analysis import format_console_report
from sample_data import build_sample_sessions
from session import Session


def main():
    print("=" * 72)
    print("SMART FITNESS SESSION ANALYZER")
    print("=" * 72)

    for title, profile, raw_observations in build_sample_sessions():
        session = Session.from_raw(profile, raw_observations)
        report = session.build_report()

        print(f"\n--- {title} ---")
        print(format_console_report(report))

    print()


if __name__ == "__main__":
    main()
