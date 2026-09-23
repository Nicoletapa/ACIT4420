# Smart Fitness Session Analyzer

**Assignment:** Python Programming Assignment (I) — Object-Oriented Analysis Systems
**Selected option:** Option A — Smart Fitness Session Analyzer

**Student name: Nicoleta Pavelescu
**Student number: 404194


## 1. Description

A fitness centre receives simulated wearable measurements from training
sessions. This program takes the raw participant and observation data
produced by the instructor-supplied `data_generator.py`, validates every
observation, compares it against the participant's personal baseline, and
classifies the session as **resting**, **moderate activity**, **high
activity**, **recovering**, or **insufficient data**. It also detects
whether the session shows recovery (heart rate and activity declining near
the end) and produces both a structured dictionary result and a readable
console report explaining the classification.

Run `python3 main.py` to see the analyzer work through the five required
minimum scenarios (resting, moderate activity, high activity, activity
followed by recovery, and poor-quality/invalid sensor data).

## 2. Project structure

```
option_a_fitness/
|-- README.md              This file
|-- main.py                 Entry point: runs the five minimum scenarios and prints reports
|-- sample_data.py           Builds the five scenarios by calling data_generator.py
|-- tests.py                 Unit tests (unittest, standard library only)
|-- requirements.txt         Empty -- standard library only
|-- data_generator.py        Instructor-supplied, unmodified
|-- example_usage.py         Instructor-supplied, unmodified
|-- DATA_DESCRIPTION.md      Instructor-supplied field reference, unmodified
|-- measurements.py          Measurement base class + one subclass per sensor field
|-- observation.py           Observation: one measurement window
|-- participant.py           Participant: identity + personal baseline
`-- session.py                Session: a participant's full set of observations, analysis, report
```

The solution is split across several small modules instead of one large
`main.py` so that each class lives with its own responsibility. `main.py`
only wires the pieces together and prints the result; it contains no
analysis logic itself.

## 3. Class design

| Class | File | Responsibility |
|---|---|---|
| `Measurement` (+ `HeartRateMeasurement`, `SkinResponseMeasurement`, `TemperatureMeasurement`, `ActivityLevelMeasurement`, `SignalQualityMeasurement`) | `measurements.py` | Wraps one raw sensor value for one field and knows whether that value is physically plausible for that field. |
| `Observation` | `observation.py` | One measurement window. Composed of five `Measurement` objects (one per field); decides whether the whole window is valid and/or reliable enough to use. |
| `Participant` | `participant.py` | A participant's identity and personal baseline (resting heart rate, skin response, temperature); computes how far a new reading sits from that baseline. |
| `Session` | `session.py` | A participant's full set of observations for one training session. Composed of one `Participant` and a list of `Observation` objects. Owns all of the analysis: usable-observation filtering, summary statistics, recovery detection, classification, and the structured report. |

Standalone functions (not tied to any one class) live in `analysis.py`:
`is_plausible` (validation), `compute_summary_statistics` and
`detect_recovery` (calculation), `explain_classification` and
`format_console_report` (presentation).

## 4. Where the OOP requirements are demonstrated

- **Composition (required, clearest example):** `Session` *has a*
  `Participant` and *has* a list of `Observation` objects
  (`session.py`); `Observation` in turn *has* one `Measurement` per field
  (`observation.py`). None of these are "is-a" relationships, so
  composition is the right tool, not inheritance.
- **Encapsulation / private-protected attribute behind a property:**
  `Participant._participant_id` is set once, validated in
  `_validated_id`, and only ever exposed through the read-only
  `participant_id` property (`participant.py`). `Observation` similarly
  keeps `_measurements` and `_timestamp` behind properties/methods rather
  than exposing them directly.
- **Inheritance and method overriding:** `HeartRateMeasurement` inherits
  from `Measurement` and overrides `_evaluate()` to add a heart-rate-specific
  rule (a wearable reports whole beats per minute, so a fractional value is
  flagged as `"non-integer-heart-rate"` even though it is numerically
  in-range) after first reusing the base class's checks via `super()`
  (`measurements.py`). The other four sensor-field classes specialise
  `Measurement` by overriding its `PLAUSIBLE_RANGE`.
- **Class method / static method with a justified purpose:**
  `Measurement.create()` is a classmethod factory that picks the right
  subclass for a field name, so calling code never needs to know the
  subclasses exist. `Session.classification_thresholds()` is a static
  method because the intensity thresholds are a fixed constant that does
  not depend on any particular session instance. `Observation.from_dict`,
  `Participant.from_profile` and `Session.from_raw` are classmethod
  alternate constructors that build the object graph directly from the
  generator's raw dictionaries.
- **Standalone functions:** five functions in `analysis.py` (see section 3)
  handle validation, calculation and presentation independently of any
  class, and are reused by both the classes and `tests.py`.

## 5. Assumptions and classification rules

- An observation is **valid** when every required field is present and
  within a physically plausible range for that field (e.g. heart rate
  30-220 bpm, activity level 0-1). It is additionally **reliable** (and
  therefore counted as "usable") only when its `signal_quality` is at
  least `0.60`; a structurally valid but low-confidence reading is
  excluded from analysis the same way a corrupted one is.
- A session needs at least **3 usable observations** to be classified at
  all; fewer than that is reported as `insufficient data`. In the
  supplied `poor_quality` scenario, every observation has
  `signal_quality` below the reliability threshold by design, so the
  session always resolves to `insufficient data` -- this is treated as
  the correct, intentional outcome for that scenario rather than a bug.
- **Recovery** is detected by comparing the first ~30% of usable
  observations (by timestamp) against the last ~30%: if the early portion
  is clearly elevated above baseline (heart rate delta ≥ 15 bpm, or
  activity ≥ 0.35) and the late portion has dropped to roughly half of
  that elevation or less, the session is classified as `recovering`. This
  check runs before the resting/moderate/high thresholds, so a session
  that starts high and ends low is reported as `recovering` rather than
  averaged into a misleading middle category.
- Otherwise, the session is classified using the average heart-rate delta
  above baseline and the average activity level across usable
  observations, against fixed thresholds in
  `Session.classification_thresholds()`:
  - **resting:** heart rate delta ≤ 12 bpm and activity ≤ 0.25
  - **moderate activity:** heart rate delta ≤ 45 bpm and activity ≤ 0.60
  - **high activity:** anything above the moderate-activity band
  - These thresholds were chosen empirically by running the generator
    across many seeds per scenario (see `tests.py` and the classification
    tests) and checking that every one of the five minimum scenarios
    classifies as intended.

## 6. Installation and running instructions

Requires Python 3.9+.

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
python3 main.py
```

To run the test suite:

```bash
python3 -m unittest tests.py -v
```

## 7. Example output

```
--- Resting session ---
Participant: P001-resting
Classification: RESTING
Observations: 12 usable / 12 total (0 rejected or flagged as unreliable)
      heart_rate: avg=63.25  min=57.00  max=67.00  (n=12)
  activity_level: avg=0.14  min=0.05  max=0.20  (n=12)
   skin_response: avg=1.84  min=1.69  max=2.00  (n=12)
     temperature: avg=32.82  min=32.65  max=32.92  (n=12)
Explanation: Based on 12 of 12 usable observations, heart rate averaged +1.2 bpm
relative to the participant's baseline and activity level averaged 0.14. Both
values stayed close to the participant's resting baseline throughout the session.

--- Poor-quality / invalid sensor data ---
Participant: P001-poor_quality
Classification: INSUFFICIENT DATA
Observations: 0 usable / 12 total (12 rejected or flagged as unreliable)
Explanation: Only 0 of 12 observations were usable (valid and reliable enough to
trust), which is below the minimum needed to classify this session.
```

The full output for all five scenarios is produced by `python3 main.py`.


