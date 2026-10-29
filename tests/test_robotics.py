"""Robotics subset test suite — quaternion / timestamp / NaN / units rules,
plus the four-field case that motivated them (public dataset review practice)."""
import json

from phm_lite_check.robotics import (
    check_quaternion,
    check_timestamps,
    check_numeric_array,
    check_units_present,
    check_robotics_record,
)


def rules(violations):
    return {v["rule"] for v in violations}


# ---------- quaternion ----------
def test_quaternion_unit_passes():
    assert check_quaternion([0.5, 0.5, 0.5, 0.5]) == []


def test_quaternion_unnormalized_fails():
    vs = check_quaternion([1.0, 0.5, 0.5, 0.5])  # |q| ~ 1.395 (public issue case)
    assert "quaternion_not_normalized" in rules([v.to_dict() for v in vs])


def test_quaternion_nan_fails():
    vs = check_quaternion([float("nan"), 0.0, 0.0, 1.0])
    assert "quaternion_nan_inf" in rules([v.to_dict() for v in vs])


def test_quaternion_wrong_shape():
    vs = check_quaternion([1.0, 0.0, 0.0])
    assert "quaternion_shape" in rules([v.to_dict() for v in vs])


# ---------- timestamps ----------
def test_timestamps_monotonic_passes():
    assert check_timestamps([0.0, 0.1, 0.2, 0.3]) == []


def test_timestamps_out_of_order_fails():
    vs = check_timestamps([0.0, 0.2, 0.1])
    assert "timestamp_not_monotonic" in rules([v.to_dict() for v in vs])


def test_timestamps_duplicate_warns():
    vs = check_timestamps([0.0, 0.1, 0.1])
    assert "timestamp_duplicates" in rules([v.to_dict() for v in vs])
    assert all(v.severity != "FAIL" for v in vs)


def test_timestamps_gap_warns():
    # median dt = 0.1; a 0.5 gap (>3x) should warn (possible frame loss)
    vs = check_timestamps([0.0, 0.1, 0.2, 0.7, 0.8])
    assert "timestamp_gap" in rules([v.to_dict() for v in vs])


# ---------- numeric arrays ----------
def test_nan_inf_scan():
    vs = check_numeric_array([1.0, float("nan"), float("inf")])
    r = rules([v.to_dict() for v in vs])
    assert "array_nan" in r and "array_inf" in r


def test_clean_array_passes():
    assert check_numeric_array([1.0, 2.0, 3.0]) == []


# ---------- units ----------
def test_missing_unit_annotation_warns():
    rec = {"position": [1.0, 2.0], "units": {}}
    vs = check_units_present(rec)
    assert "unit_missing" in rules([v.to_dict() for v in vs])


def test_annotated_unit_passes():
    rec = {"position": [1.0, 2.0], "units": {"position": "m"}}
    assert check_units_present(rec) == []


# ---------- full record ----------
def test_full_record_all_good():
    rec = {
        "quaternion": [0.5, 0.5, 0.5, 0.5],
        "timestamps": [0.0, 0.1, 0.2],
        "position": [1.0, 2.0, 3.0],
        "units": {"position": "m"},
    }
    out = check_robotics_record(rec)
    assert out["verdict"] == "PASS"
    assert out["summary"]["deterministic"] is True


def test_full_record_bad_quaternion_fails():
    rec = {"quaternion": [1.395, 0.0, 0.0, 0.0]}
    out = check_robotics_record(rec)
    assert out["verdict"] == "FAIL"


def test_report_is_json_serializable():
    rec = {"quaternions": [[0.5, 0.5, 0.5, 0.5], [1.2, 0.0, 0.0, 0.0]],
           "timestamps": [0.0, 0.1, 0.05]}
    out = check_robotics_record(rec)
    s = json.dumps(out)  # must not raise
    assert "FAIL" in s
