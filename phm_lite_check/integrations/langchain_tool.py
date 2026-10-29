# -*- coding: utf-8 -*-
"""LangChain tool adapter for phm_lite_check.

Usage:
    from phm_lite_check.integrations import langchain_tool
    tools = langchain_tool.get_langchain_tools()
    # then pass `tools` to your agent's tool list

Requires: langchain-core (installed separately, not a hard dependency).
"""

import json
from typing import List

from ..checker import check_text, check_quantity  # noqa: F401
from ..robotics import check_robotics_record  # noqa: F401


def _err(msg: str) -> str:
    return json.dumps({"verdict": "FAIL",
                       "violations": [{"rule": "input_format", "severity": "FAIL",
                                       "detail": msg}]})


def get_langchain_tools() -> List:
    """Build LangChain @tool callables. Raises ImportError with guidance
    if langchain-core is not installed."""
    try:
        from langchain_core.tools import tool  # type: ignore
    except ImportError as e:
        raise ImportError(
            "langchain-core is required for this adapter: "
            "pip install langchain-core"
        ) from e

    @tool
    def physics_text_check(text: str) -> str:
        """Check LLM-generated text for physically implausible numeric claims
        (deterministic offline checker).

        Input: any text containing quantity statements, e.g.
        'The drone descends at 450 km/h and confidence is 1.8'.
        Extracts quantities with known units and checks them: unit
        consistency, speed-of-light limit, absolute zero, non-negativity,
        probability range, kinematic relations.
        Returns JSON: verdict PASS/WARN/FAIL + structured violations.
        """
        return json.dumps(check_text(text))

    @tool
    def physics_quantity_check(value: float, unit: str) -> str:
        """Check one numeric quantity against physical law (deterministic offline checker).

        Input: value (number) and unit (string, SI or common units).
        Example: value=450, unit='km/h'.
        Returns JSON: verdict PASS/WARN/FAIL + structured violations.
        """
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return _err(f"value must be a number, got {type(value).__name__}")
        result = {"verdict": "PASS", "violations": [v.to_dict() for v in
                                                    check_quantity(float(value), str(unit))],
                  "engine": "PHM-Lite", "deterministic": True}
        if any(v["severity"] == "FAIL" for v in result["violations"]):
            result["verdict"] = "FAIL"
        elif any(v["severity"] == "WARN" for v in result["violations"]):
            result["verdict"] = "WARN"
        return json.dumps(result)

    @tool
    def robotics_data_check(record_json: str) -> str:
        """Check a robotics dataset record for physical plausibility (deterministic offline checker).

        Input: JSON object with optional keys: 'quaternion' or 'quaternions'
        (list of [w,x,y,z]), 'timestamps' (numeric list), 'units' (dict),
        plus any numeric arrays to NaN/Inf-scan.
        Returns JSON: verdict PASS/WARN/FAIL + structured violations + summary.
        """
        try:
            payload = json.loads(record_json)
        except json.JSONDecodeError as e:
            return _err(f"invalid JSON: {e}")
        return json.dumps(check_robotics_record(payload))

    return [physics_text_check, physics_quantity_check, robotics_data_check]
