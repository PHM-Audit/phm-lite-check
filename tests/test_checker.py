"""PHM-Lite core test suite — every rule + determinism guarantee.
Written against the real API: check_kinematics/check_conservation return
List[Violation]; check_text/full_check return verdict dicts."""
import json
import subprocess
import sys
from pathlib import Path

from phm_lite_check.checker import (  # noqa: E402
    check_conservation,
    check_kinematics,
    check_text,
    to_si,
    full_check,
)


def sev_of(vs):
    if any(v.severity == "FAIL" for v in vs):
        return "FAIL"
    if any(v.severity == "WARN" for v in vs):
        return "WARN"
    return "PASS"


def v_of(text):
    return check_text(text)["verdict"]


# ---------- FAIL rules via text scan ----------
def test_speed_of_light():
    r = check_text("travels at 4.0e9 m/s")
    assert r["verdict"] == "FAIL"
    assert any(v["rule"] == "speed_exceeds_light" for v in r["violations"])

def test_negative_mass():
    assert v_of("mass = -3 kg") == "FAIL"

def test_absolute_zero():
    assert v_of("cooled to -300 degC") == "FAIL"

def test_probability():
    assert v_of("confidence: 1.8") == "FAIL"

# ---------- kinematics: relation cross-check ----------
def test_kinematics_violation():
    vs = check_kinematics({"v0": 0.0, "a": 9.8, "t": 3.0, "v": 50.0})
    assert sev_of(vs) == "FAIL"
    assert any(v.rule == "kinematics_v_equation" for v in vs)

def test_freefall_consistent():
    vs = check_kinematics({"v0": 0.0, "a": 9.8, "t": 3.0, "v": 29.4})
    assert sev_of(vs) == "PASS"

# ---------- conservation ----------
def test_energy_not_conserved():
    vs = check_conservation({"energy": 100.0}, {"energy": 150.0})
    assert sev_of(vs) == "FAIL"
    assert any(v.rule == "conservation_energy" for v in vs)

def test_energy_conserved():
    vs = check_conservation({"energy": 100.0}, {"energy": 101.0})
    assert sev_of(vs) == "PASS"

# ---------- units ----------
def test_unit_conversion_kmh():
    assert abs(to_si(18.0, "km/h")[0] - 5.0) < 1e-9

def test_unit_conversion_mph():
    assert abs(to_si(1.0, "mph")[0] - 0.44704) < 1e-9

def test_unknown_unit_ignored():
    assert to_si(1.0, "flibbity") == (None, None)
    assert v_of("flux 42 flibbity per squank") == "PASS"

# ---------- determinism: two runs byte-identical ----------
def test_determinism_two_runs():
    text = "descends at 450 km/h, battery 5 kWh, confidence: 1.8"
    kw = dict(kinematics={"v0": 0.0, "a": 9.8, "t": 3.0, "v": 50.0})
    a = full_check(text, **kw)
    b = full_check(text, **kw)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

# ---------- CLI demo runs ----------
def test_cli_demo():
    out = subprocess.run(
        [sys.executable, str(Path(__file__).parent.parent / "phm_lite_check" / "checker.py")],
        capture_output=True, text=True, timeout=30)
    assert out.returncode == 0
    j = json.loads(out.stdout)
    assert j["deterministic"] is True
