# Shipment Exception Resolution Agent (V1)

An autonomous agent that investigates a delayed/at-risk container
shipment, decides WHICH checks to run based on symptoms (not a fixed
checklist), proposes a resolution, and — critically — has that
proposal validated by **deterministic code, not the LLM itself**
before anything is committed. High-risk cases are escalated to a
human instead of being auto-resolved.

Modeled on real logistics "control tower" use cases: exception
detection, automated customer notification, human-in-the-loop
approval for risky decisions.

## Why it's agentic, not a script

The agent isn't told "always check port, then weather, then customs."
The LLM decides which diagnostic tool to call next based on what it
learns — a customs-flagged shipment might skip weather entirely.
Order and number of steps vary per case.

## The safety pattern: LLM proposes, code validates

This is the core engineering idea in this project:

```
        Agent (LLM)
             │
             ▼
      propose_reroute()          <- LLM's recommendation
             │
             ▼
     verify_eta_feasible()       <- deterministic date-math check
             │
             ▼
     assess_risk_level()         <- deterministic rule-based tier
      ┌──────┴──────┐
    LOW/MEDIUM      HIGH
      │               │
      ▼               ▼
  Auto-resolve    Escalate to human
  (RESOLVED)      (PENDING_HUMAN_APPROVAL)
```

`assess_risk_level` is plain if/else logic — the LLM cannot override
it, and the system prompt explicitly forbids arguing with it. See
`tests/test_risk.py::test_bad_recommendation_is_caught` for the exact
scenario this guards against: even if the LLM's reasoning were wrong,
the deterministic check still flags it.

## Architecture

```
        FastAPI (api/main.py)              Agent (agent/main.py, MCP client)
              │                                       │
              └───────────────┬───────────────────────┘
                               ▼
                    core/  (shared repository layer)
                    ├── db.py       (DynamoDB: live shipment state)
                    └── storage.py  (S3: notifications / audit trail)
                               ▲
                               │
              mcp_server/  (MCP server, tools call into core/)
              ├── shipment_tools.py, port_tools.py, customs_tools.py
              ├── weather_tools.py     (REAL live Open-Meteo API call)
              ├── routing_tools.py     (propose_reroute, verify_eta_feasible)
              ├── risk_tools.py        (deterministic guardrail)
              └── notify_tools.py
```

The API and the agent both go through the same `core/` layer — no
duplicated DynamoDB/S3 logic between the two.

## Repo structure

```
maersk-shipment-agent/
├── core/                # shared DynamoDB + S3 repository layer
│   ├── db.py
│   └── storage.py
├── mcp_server/
│   ├── server.py
│   └── tools/           # each tool is a thin wrapper calling core/
├── agent/
│   ├── main.py          # ReAct loop, also importable as run_agent()
│   ├── prompts.py
│   ├── state.py
│   └── reasoning.py
├── api/
│   └── main.py           # FastAPI: POST/GET /shipments endpoints
├── tests/
│   ├── test_routing.py   # pure logic, no AWS needed
│   ├── test_risk.py      # the guardrail tests
│   ├── test_agent_state.py
│   └── test_core.py      # moto-mocked DynamoDB/S3, no real AWS needed for CI
├── scripts/setup_aws.py  # creates real AWS resources + seeds demo data
├── docker/Dockerfile.agent
└── docker-compose.yml
```

## REST API

| Method | Path | Purpose |
|---|---|---|
| POST | `/shipments` | Create a new shipment record |
| GET | `/shipments/{id}` | Get full shipment details |
| GET | `/shipments/{id}/status` | Get just status/eta/notes |
| POST | `/shipments/{id}/investigate` | Trigger the agent to investigate + resolve/escalate |
| POST | `/shipments/{id}/resolve` | Human approves/rejects an escalated (PENDING_HUMAN_APPROVAL) shipment |

## Setup

```bash
# 1. AWS credentials (free tier covers this)
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=ap-south-1
export AWS_S3_BUCKET=your-unique-bucket-name

# 2. Ollama
ollama pull qwen2.5-coder:7b

# 3. Install deps
pip install -r requirements.txt

# 4. Create AWS resources + seed synthetic shipment data
python scripts/setup_aws.py

# 5a. Run the agent directly (CLI)
python agent/main.py --container-id MAEU1234567

# 5b. OR run the API and trigger it over HTTP
uvicorn api.main:app --reload
curl -X POST http://localhost:8000/shipments/MAEU1234567/investigate
```

## Testing

```bash
pytest tests/ -v
```

- `test_routing.py`, `test_risk.py` — pure deterministic logic, no AWS/LLM needed
- `test_agent_state.py` — the guardrail that blocks "finish" without required AWS steps
- `test_core.py` — DynamoDB/S3 behavior, mocked with `moto` (free, no real AWS account needed) so this runs in CI without secrets

## Imp Notes

- "Tool selection is dynamic — the agent decides which signal to
  investigate first based on the shipment's actual state, not a fixed order."
- "The LLM's recommendation is never trusted blindly — a deterministic
  risk-tier function validates it, and HIGH risk always routes to a
  human via PENDING_HUMAN_APPROVAL, not auto-resolution."
- "The API and the agent share one repository layer (`core/`), so
  there's a single source of truth for shipment state."
- "AWS isn't a bolt-on — DynamoDB holds live state, S3 holds the audit
  trail, and both are required for the agent to report success."
- Roadmap: "V2 would add Kafka so the agent is event-triggered
  (`shipment.eta_at_risk`, `shipment.customs_hold`) instead of an API
  call; V3 would add Kubernetes + observability once the core logic
  is proven."
