# phm-lite-check

Deterministic physics plausibility checking for **LLM outputs** and
**robotics / embodied-AI datasets**. Zero dependencies, pure standard
library, Python >= 3.8.

This package is an **independent, community-provided library**: it is the
offline subset of the PHM physical-judgment engine (proprietary core
methods are intentionally excluded). A companion plugin
(`phm-physics-check`) is listed on the Dify Marketplace.

> Not affiliated with, endorsed by, or sponsored by LangChain, AutoGen,
> or Dify. Integration adapters are community-provided.

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

```bash
pip install phm-lite-check          # core (zero dependencies)
pip install "phm-lite-check[langchain]"   # + langchain-core
pip install "phm-lite-check[autogen]"     # + autogen-agentchat
```

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

## License

MIT
