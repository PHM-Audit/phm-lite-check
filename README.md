# phm-lite-check

[![PHM Physics Check MCP server](https://mcprush.com/badge/phm-physics-check-mcp/card.svg)](https://mcprush.com/to/phm-physics-check-mcp?ref=badge)

<!-- mcp-name: io.github.PHM-Audit/phm-lite-check -->

Deterministic physics plausibility checking for **LLM outputs** and
**robotics / embodied-AI datasets**. Zero dependencies, pure standard
library, Python >= 3.8.

This package is an **independent, community-provided library**: it is the
offline subset of the PHM physical-judgment engine (proprietary core
methods are intentionally excluded). A companion plugin
(`phm-physics-check`) is listed on the Dify Marketplace.

> Not affiliated with, endorsed by, or sponsored by LangChain, AutoGen,
> or Dify. Integration adapters are community-provided.

## Approved by the PyRIT creator — microsoft/PyRIT

A scorer wrapper of this package lives in
**[microsoft/PyRIT PR #3507](https://github.com/microsoft/PyRIT/pull/3507)**
(`physics_consistency_scorer`). Status as of 2026-11-10:

- Six first-round correctness issues (maintainer + automated reviewer) were
  fixed same-day (2026-11-08).
- The PyRIT creator (richlundeen) **approved the PR** ("no blocking concerns
  remain"), verified 356 scoped tests, Ruff and the scoped type check.
- He then pushed follow-up integration commits **on this PR's branch**:
  an upstream-main merge to clear conflicts (eb8948e) and a hook adaptation
  to the new `ScoringExpectation` scorer API with documented numeric checks
  (8a163d9).
- The PR remains open pending the maintainer's merge; nothing is left open
  on this side.

## Claimed on MCPush

Ownership-verified listing approved on [MCPush](https://mcprush.com/to/phm-physics-check-mcp): security grade A, 3 tools, no sign-in required, local & free (v1.0.1).

## What it checks

### Text / quantities (`check_text`, `full_check`)
- Dimensional / unit consistency (SI + common units)
- Universal speed limit (c)
- Absolute temperature floor (0 K)
- Non-negativity of mass / length / energy
- Probability range [0, 1]
- Kinematic relations (free-fall family, tolerance-checked)
- Conservation checks (energy / momentum, tolerance-checked)

### Robotics records (`check_robotics_record`)
- Quaternion normalization (|q| within tolerance of 1.0)
- Timestamp sanity: monotonicity, duplicates, NaN/Inf, outlier gaps
  (possible frame loss)
- NaN / Inf scan over numeric arrays
- Unit annotation presence for common motion fields

## Design guarantees

- **Deterministic**: same input -> same output, always reproducible.
- **Zero dependencies**: pure standard library; framework adapters import
  their host lazily.
- **Verdicts**: PASS / WARN / FAIL with structured violation records.
- **No network calls**: everything runs offline in-process.

> NOTE: this package contains only the deterministic offline subset of the
> PHM physical-judgment engine. Proprietary core methods are intentionally
> excluded. (Deployment-specific deep checks are available separately via a
> configurable remote engine endpoint, not included in this package.)

## Install

**Option A — from the GitHub repo** (no package index needed):

```bash
pip install git+https://github.com/PHM-Audit/phm-lite-check
```

**Option B — from a Release wheel** (faster, no git clone):

```bash
pip install https://github.com/PHM-Audit/phm-lite-check/releases/download/v1.0.0/phm_lite_check-1.0.0-py3-none-any.whl
```

**Optional extras** (once installed):

```bash
pip install "phm-lite-check[langchain]"   # + langchain-core (adapter tests)
pip install "phm-lite-check[autogen]"     # + autogen-agentchat
```

PyPI listing is planned; both options above work today.

## Quickstart — library

```python
from phm_lite_check import check_text, check_robotics_record

check_text("The drone descends at 450 km/h and confidence is 1.8.")
# {"verdict": "FAIL", "violations": [...], ...}

check_robotics_record({
    "quaternion": [1.395, 0.0, 0.0, 0.0],   # |q| >> 1 -> FAIL
    "timestamps": [0.0, 0.1, 0.05],          # not monotonic -> FAIL
    "position": [1.0, 2.0],                  # no unit annotated -> WARN
})
```

## Quickstart — LangChain

```python
from phm_lite_check.integrations import langchain_tool

tools = langchain_tool.get_langchain_tools()   # 3 @tool callables
agent = create_react_agent(llm, tools)         # your usual wiring
```

## Quickstart — AutoGen (v0.4+)

```python
from autogen_agentchat.agents import AssistantAgent
from phm_lite_check.integrations import autogen_tool

assistant = AssistantAgent(
    name="checked_assistant",
    model_client=...,                    # your model client
    tools=autogen_tool.get_autogen_tools(),
)
```

## Quickstart — MCP server (stdio)

The package ships a Model Context Protocol server entry point (`phm_lite_check/mcp_server.py`,
FastMCP, **stdio transport**). Works with Claude Desktop, Cursor, Cline or any MCP host.

Install with the MCP extra (requires `mcp>=1.0,<2` — the 2.x SDK renamed the FastMCP API):

```bash
pip install "phm-lite-check[mcp]"
```

Run the server:

```bash
python3 -m phm_lite_check.mcp_server
```

Claude Desktop / generic MCP host configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "phm-lite-check": {
      "command": "python3",
      "args": ["-m", "phm_lite_check.mcp_server"]
    }
  }
}
```

Tools exposed over MCP (all declared `readOnlyHint`):

| Tool | Input | Checks |
|---|---|---|
| `physics_text_check` | `{"text": "..."}` | unit inconsistency, lightspeed violations, probabilities outside [0,1], kinematic impossibilities |
| `physics_quantity_check` | `{"value": 5.5, "unit": "km/s"}` | per-quantity physical bounds |
| `robotics_data_check` | `{"record_json": "{...}"}` | quaternion normalization, timestamp sanity, NaN/Inf scan, unit annotation |

Verified end-to-end on `mcp` 1.30.0: JSON-RPC initialize handshake, `tools/list` returns the three
tools above, and a `tools/call` round-trip on `physics_quantity_check` executes against the local
rule table. The server makes zero network calls.

Also packaged as an MCPB bundle and listed in the official MCP Registry
(`io.github.PHM-Audit/phm-lite-check@1.0.1`, stdio).

## Tools exposed by both adapters

| Tool | Input | Checks |
|------|-------|--------|
| `physics_text_check` | free text with quantities | unit consistency, limits, probabilities |
| `physics_quantity_check` | value + unit | one quantity against physical law |
| `robotics_data_check` | JSON record | quaternions, timestamps, NaN/Inf, units |

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -q
```


## Third-party trial feedback

Independent trial reports of phm-lite-check are welcome. Published reports
carry attribution exactly as the author prefers (handle, real name, or org).

Report template — fill in only what you actually ran, and mark anything you
did not run as **not tested**. No estimated or extrapolated numbers:

- **Environment**: OS / Python version / framework versions
- **Install**: exact command(s) and wall-clock install time
- **Package test suite**: command used, pass count / total
- **Integration example**: what you ran (workflow / cookbook / adapter),
  one representative input, and the observed exit state (PASS / DEGRADE / VETO)
- **False-positive traps**: the spec trap cases you exercised and observed behavior
- **What was NOT tested**: explicit list, so readers can see the boundary
- **Attribution**: name/handle as you want it spelled

Submission paths:

1. Post the report in the relevant integration thread (for example
   run-llama/llama_index#24094) and we will mirror it into this section.
2. Open a PR adding `docs/trials/<handle>-<date>.md`.


## License

MIT

## Benchmark

The judgment rules shipped here are exercised in public by **[DPC-Bench v0.2](https://github.com/PHM-Audit/dpc-bench)** — a paired clean/corrupted physical-consistency detection benchmark (7 task families incl. a real NGSIM I-80 family, three-caliber L1/L2/L3 labels).
