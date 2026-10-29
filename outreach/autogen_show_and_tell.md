# phm-lite-check — deterministic physics plausibility tools for AutoGen agents

Sharing a small open-source package I built: `phm-lite-check` — three deterministic, offline checkers wrapped as AutoGen v0.4 tools. Zero runtime dependencies (pure standard library), no network calls, no model calls.

## The problem it addresses

Agents routinely produce numeric claims ("the drone descends at 450 km/h, confidence 1.8") and consume robotics/embodied-AI datasets. Some failures are purely mechanical — a probability of 1.8, a quaternion with norm 1.395, a negative mass, a timestamp sequence that goes backwards. These don't need an LLM to catch; a deterministic rule set catches them reliably and reproducibly.

## Tools exposed (plain Python functions, usable with `AssistantAgent(tools=[...])`)

- `physics_text_check(text)` — scans text for physically implausible quantities: unit consistency, universal speed limit, absolute zero floor, non-negativity of mass/energy, probability range [0,1], kinematic relations, conservation checks
- `physics_quantity_check(value, unit)` — one quantity against physical law
- `robotics_data_check(record_json)` — robotics dataset records: quaternion normalization, timestamp monotonicity/duplicates/outlier gaps (possible frame loss), NaN/Inf scan, unit annotation presence

Verdicts are structured: `PASS / WARN / FAIL` with per-violation records (rule, severity, detail, location).

## Quickstart

```bash
pip install git+https://github.com/PHM-Audit/phm-lite-check
```

```python
from autogen_agentchat.agents import AssistantAgent
from phm_lite_check.integrations import autogen_tool

assistant = AssistantAgent(
    name="checked_assistant",
    model_client=your_model_client,
    tools=autogen_tool.get_autogen_tools(),
)
```

Actual output of `physics_text_check("The drone descends at 450 km/h, confidence 1.8.")`:

```json
{
 "verdict": "FAIL",
 "n_quantities_checked": 2,
 "violations": [
  {"rule": "probability_out_of_range", "severity": "FAIL",
   "detail": "Probability 1.8 outside [0, 1]", "location": "confidence 1.8"}
 ],
 "engine": "PHM-Lite", "version": "1.0.0", "deterministic": true
}
```

## Scope and limits

- This is the deterministic offline subset of a larger physical-judgment engine (the PHM engine); proprietary deep-check methods are intentionally excluded. The offline subset covers mechanical/deterministic checks only — it does not perform statistical or learned validation, and it does not reason about context-dependent physical plausibility.
- Determinism: same input yields the same output under the same package version.
- 36 tests pass; the LangChain adapter tests additionally run against langchain-core 1.7.1 (an optional dependency, not required at runtime). Reproduce: `pip install -e ".[dev]" && pytest tests/ -q`

Not affiliated with, endorsed by, or sponsored by Microsoft or the AutoGen team — just a community tool that plugs into the standard `tools=[...]` interface.

Repo: https://github.com/PHM-Audit/phm-lite-check
