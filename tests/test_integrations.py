"""Adapter-layer tests. AutoGen adapter is plain functions (always testable);
LangChain adapter tests run only if langchain-core is installed."""
import json

from phm_lite_check.integrations import autogen_tool


def _rules(out_json: str):
    return {v["rule"] for v in json.loads(out_json).get("violations", [])}


# ---------- autogen tools (plain functions) ----------
def test_autogen_tools_count():
    tools = autogen_tool.get_autogen_tools()
    assert len(tools) == 3
    assert all(callable(t) for t in tools)


def test_autogen_physics_text_check():
    out = autogen_tool.physics_text_check("The drone descends at 450 km/h.")
    r = json.loads(out)
    assert r["verdict"] in ("PASS", "WARN")
    assert r["n_quantities_checked"] == 1


def test_autogen_physics_text_check_bad_probability():
    out = autogen_tool.physics_text_check("confidence is 1.8 probability of success.")
    r = _rules(out)
    assert "probability_out_of_range" in r or "prob_out_of_range" in r


def test_autogen_quantity_check_fails_light_speed():
    out = autogen_tool.physics_quantity_check(3.0e8, "m/s")
    r = json.loads(out)
    assert r["verdict"] == "FAIL"


def test_autogen_quantity_check_bad_value_type():
    out = autogen_tool.physics_quantity_check("abc", "m/s")
    assert json.loads(out)["violations"][0]["rule"] == "input_format"


def test_autogen_robotics_check_fails_on_bad_quat():
    out = autogen_tool.robotics_data_check('{"quaternion": [1.395, 0.0, 0.0, 0.0]}')
    r = json.loads(out)
    assert r["verdict"] == "FAIL"


def test_autogen_robotics_check_bad_json():
    out = autogen_tool.robotics_data_check("{not json")
    assert json.loads(out)["violations"][0]["rule"] == "input_format"


# ---------- langchain tools (optional dep) ----------
def test_langchain_adapter_importable_or_clear_error():
    try:
        import langchain_core  # noqa: F401
        have_lc = True
    except ImportError:
        have_lc = False
    from phm_lite_check.integrations import langchain_tool
    if have_lc:
        tools = langchain_tool.get_langchain_tools()
        assert len(tools) == 3
        out = tools[0].invoke({"text": "confidence is 1.8"})
        assert json.loads(out)["verdict"] in ("FAIL", "WARN", "PASS")
    else:
        # must raise ImportError with pip guidance, not crash oddly
        try:
            langchain_tool.get_langchain_tools()
            raised = False
        except ImportError as e:
            raised = "pip install langchain-core" in str(e)
        assert raised
