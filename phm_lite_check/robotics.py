#!/usr/bin/env python3
"""
Deterministic robotics / embodied-AI dataset plausibility checks.

Deterministic engineering rules distilled from public dataset review practice:
  - Quaternion normalization (unit quaternions, tolerance-checked)
  - Timestamp sanity (monotonicity, duplicates, NaN, outlier gaps)
  - NaN / Inf scan for numeric arrays
  - Unit annotation presence for common motion fields
  - Frame-loss detection via median-interval gap analysis

Design guarantees (same as checker.py):
  - Deterministic: same input -> same output.
  - Zero dependencies (pure standard library), Python >= 3.8.
  - Verdicts: PASS / WARN / FAIL with structured violation records.

NOTE: This is the OFFLINE SUBSET of the PHM physical-judgment engine.
It intentionally excludes proprietary core methods; deep checks are
exposed via a configurable remote engine endpoint.
"""

import math
from typing import Any, Dict, List, Optional, Sequence

from .checker import Violation, _verdict

__all__ = [
    "check_quaternion",
    "check_timestamps",
    "check_numeric_array",
    "check_units_present",
    "check_robotics_record",
]

# Tolerances (engineering judgment, publicly defensible)
QUAT_NORM_TOL = 0.01        # |q| must be within 1% of 1.0
GAP_OUTLIER_FACTOR = 3.0    # dt > 3x median dt => suspicious gap

COMMON_MOTION_FIELDS = {
    "position": ("m", "meter", "mm", "cm", "km"),
    "velocity": ("m/s", "mps", "km/h", "mm/s"),
    "acceleration": ("m/s^2", "m/s2", "g"),
    "force": ("N", "newton"),
    "torque": ("N.m", "Nm", "N*m"),
    "angle": ("rad", "deg", "degree"),
    "angular_velocity": ("rad/s", "deg/s", "rpm"),
}


def check_quaternion(q: Sequence[float], location: str = "quaternion") -> List[Violation]:
    """Unit-quaternion check: |q| must stay within tolerance of 1.0."""
    v: List[Violation] = []
    if len(q) != 4:
        v.append(Violation("quaternion_shape", "FAIL",
                           f"expected 4 components, got {len(q)}", location))
        return v
    vals = []
    for x in q:
        if not isinstance(x, (int, float)) or isinstance(x, bool):
            v.append(Violation("quaternion_type", "FAIL",
                               f"non-numeric component: {x!r}", location))
            return v
        vals.append(float(x))
    if any(math.isnan(x) or math.isinf(x) for x in vals):
        v.append(Violation("quaternion_nan_inf", "FAIL",
                           "quaternion contains NaN/Inf", location))
        return v
    norm = math.sqrt(sum(x * x for x in vals))
    if not (abs(norm - 1.0) <= QUAT_NORM_TOL):
        v.append(Violation("quaternion_not_normalized", "FAIL",
                           f"|q|={norm:.6f} deviates from 1.0 beyond tol {QUAT_NORM_TOL}",
                           location))
    return v


def check_timestamps(ts: Sequence[float], location: str = "timestamps") -> List[Violation]:
    """Timestamp sanity: monotonic, finite, no duplicates, no outlier gaps."""
    v: List[Violation] = []
    if len(ts) < 2:
        return v
    vals = []
    for x in ts:
        if not isinstance(x, (int, float)) or isinstance(x, bool):
            v.append(Violation("timestamp_type", "FAIL",
                               f"non-numeric timestamp: {x!r}", location))
            return v
        vals.append(float(x))
    if any(math.isnan(x) or math.isinf(x) for x in vals):
        v.append(Violation("timestamp_nan_inf", "FAIL",
                           "timestamp series contains NaN/Inf", location))
        return v
    # monotonicity
    for i in range(1, len(vals)):
        if vals[i] < vals[i - 1]:
            v.append(Violation("timestamp_not_monotonic", "FAIL",
                               f"t[{i}]={vals[i]!r} < t[{i-1}]={vals[i-1]!r}", location))
            break
    # duplicates
    dup = sum(1 for i in range(1, len(vals)) if vals[i] == vals[i - 1])
    if dup:
        v.append(Violation("timestamp_duplicates", "WARN",
                           f"{dup} duplicated timestamp(s)", location))
    # gaps
    dts = [vals[i] - vals[i - 1] for i in range(1, len(vals)) if vals[i] > vals[i - 1]]
    if dts:
        s = sorted(dts)
        med = s[len(s) // 2]
        if med > 0:
            for i, dt in enumerate(dts):
                if dt > GAP_OUTLIER_FACTOR * med:
                    v.append(Violation("timestamp_gap", "WARN",
                                       f"dt={dt:.6g} > {GAP_OUTLIER_FACTOR}x median {med:.6g} "
                                       f"(possible frame loss at index {i})", location))
                    break  # one representative warning is enough
    return v


def check_numeric_array(arr: Sequence[Any], location: str = "array") -> List[Violation]:
    """NaN / Inf scan over a numeric array (non-numeric entries reported)."""
    v: List[Violation] = []
    for i, x in enumerate(arr):
        if isinstance(x, bool):
            continue
        if not isinstance(x, (int, float)):
            v.append(Violation("array_type", "WARN",
                               f"non-numeric entry at [{i}]: {type(x).__name__}", location))
            continue
        xf = float(x)
        if math.isnan(xf):
            v.append(Violation("array_nan", "FAIL", f"NaN at [{i}]", location))
        elif math.isinf(xf):
            v.append(Violation("array_inf", "FAIL", f"Inf at [{i}]", location))
    return v


def check_units_present(record: Dict[str, Any], location: str = "record") -> List[Violation]:
    """Warn when common motion fields lack unit annotations."""
    v: List[Violation] = []
    units_map = record.get("units", {}) if isinstance(record, dict) else {}
    if not isinstance(record, dict):
        return v
    for field, _known in COMMON_MOTION_FIELDS.items():
        if field in record and field not in units_map:
            v.append(Violation("unit_missing", "WARN",
                               f"field '{field}' present but no unit annotated "
                               f"(units map missing key)", f"{location}.{field}"))
    return v


def check_robotics_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Full plausibility check for one robotics dataset record.

    Expected optional keys:
      - quaternion(s): single [w,x,y,z] or list of them
      - timestamps: sequence of numbers
      - numeric arrays: any list of numbers (all scanned)
      - units: dict mapping field -> unit string
    Returns {"verdict": PASS|WARN|FAIL, "violations": [...], "summary": {...}}.
    """
    violations: List[Violation] = []
    quats_scanned = 0
    arrays_scanned = 0

    if not isinstance(record, dict):
        violations.append(Violation("record_type", "FAIL",
                                    "record must be a dict", "root"))
    else:
        qs = record.get("quaternions", record.get("quaternion"))
        if qs is not None:
            if qs and isinstance(qs[0], (list, tuple)):
                for i, q in enumerate(qs):
                    violations.extend(check_quaternion(q, f"quaternions[{i}]"))
                    quats_scanned += 1
            elif qs:
                violations.extend(check_quaternion(qs, "quaternion"))
                quats_scanned += 1
        ts = record.get("timestamps")
        if ts is not None and isinstance(ts, (list, tuple)):
            violations.extend(check_timestamps(ts))
        for k, val in record.items():
            if k in ("quaternion", "quaternions", "timestamps", "units"):
                continue
            if isinstance(val, (list, tuple)) and val and all(
                    isinstance(x, (int, float)) and not isinstance(x, bool) for x in val[:32]):
                violations.extend(check_numeric_array(val, k))
                arrays_scanned += 1
        violations.extend(check_units_present(record))

    verdict = _verdict(violations)
    return {
        "verdict": verdict,
        "violations": [x.to_dict() for x in violations],
        "summary": {
            "engine": "PHM-Lite",
            "mode": "robotics-dataset-subset",
            "quaternions_scanned": quats_scanned,
            "numeric_arrays_scanned": arrays_scanned,
            "n_violations": len(violations),
            "deterministic": True,
        },
    }
