#!/usr/bin/env python3
"""MCP server entrypoint for phm-lite-check.

Exposes the deterministic physics plausibility checkers as Model Context
Protocol tools over stdio transport (Claude Desktop / Cursor / Cline / any
MCP host).

Requires the `mcp` package:  pip install "phm-lite-check[mcp]"
Run:                          python3 -m phm_lite_check.mcp_server
"""
import json

from mcp.server.fastmcp import FastMCP

from .checker import check_text, check_quantity
from .robotics import check_robotics_record

mcp = FastMCP("phm-lite-check")


@mcp.tool(title="Physics text check", readOnlyHint=True)
def physics_text_check(text: str) -> str:
    """Scan free text for implausible numeric claims: unit inconsistency,
    speed-of-light violations, probabilities outside [0, 1], kinematic
    impossibilities. Deterministic, offline.

    Args:
        text: any text containing numbers with units
    """
    return json.dumps(check_text(text))


@mcp.tool(title="Physics quantity check", readOnlyHint=True)
def physics_quantity_check(value: float, unit: str) -> str:
    """Validate one quantity against physical law (speed-of-light limit,
    temperature floor, probability range, kinematic relations).

    Args:
        value: numeric value
        unit: unit string, e.g. "km/s", "K", "kg"
    """
    return json.dumps(check_quantity(value, unit))


@mcp.tool(title="Robotics data check", readOnlyHint=True)
def robotics_data_check(record_json: str) -> str:
    """Check a robotics / embodied-AI dataset record for physical plausibility:
    quaternion normalization, timestamp sanity, NaN/Inf scan, unit annotation.

    Args:
        record_json: JSON object with optional keys 'quaternion'/'quaternions',
                     'timestamps', 'units', plus numeric arrays
    """
    try:
        payload = json.loads(record_json)
    except json.JSONDecodeError as e:
        return json.dumps({"verdict": "FAIL",
                           "violations": [{"rule": "input_format", "severity": "FAIL",
                                           "detail": f"invalid JSON: {e}"}]})
    return json.dumps(check_robotics_record(payload))


if __name__ == "__main__":
    mcp.run()
