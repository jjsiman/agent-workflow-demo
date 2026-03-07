# Agentrics Demo — Customer Support Pipeline

A demo that simulates a realistic multi-agent AI workflow and tracks costs in [Agentrics](http://localhost:3000).

## What it does

Runs 5–8 support tickets through a 3-agent pipeline:

| Agent | Model | Role |
|---|---|---|
| `classifier-agent` | Claude Haiku | Classifies ticket urgency/category |
| `research-agent` | GPT-4o mini | Looks up relevant policies/docs |
| `response-writer` | Claude 3.5 Sonnet | Drafts the customer reply |

No real AI API keys are needed — token usage is simulated with realistic distributions. All executions are tracked in your Agentrics dashboard.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your API key**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and paste your API key from the Agentrics dashboard → Settings → API Keys.

3. **Start the Agentrics dev server** (in the `agent-cost-optimizer` repo)
   ```bash
   npm run dev
   ```

4. **Run the demo**
   ```bash
   python demo.py
   ```

## Example output

```
Agentrics Demo — Customer Support Pipeline
Dashboard: http://localhost:3000/dashboard
Tracking:  http://localhost:3000/api/track

Running 6 support tickets through the 3-agent pipeline...

  Run #1: "My order hasn't arrived and it's been 2 weeks."
    [classifier-agent] 312→87 tokens | $0.0000
    [research-agent] 743→418 tokens | $0.0000
    [response-writer] 1204→562 tokens | $0.0006
  ...

Done! Check your dashboard to see cost breakdowns by agent.
  http://localhost:3000/dashboard
```
