"""
Agentrics Demo — Customer Support Pipeline

Simulates a 3-agent pipeline that a customer might run:
  1. Classifier Agent  — reads a ticket, classifies urgency/category  (Claude Haiku)
  2. Research Agent    — looks up relevant info based on classification (GPT-4o mini)
  3. Response Writer   — drafts a customer-facing reply                (Claude 3.5 Sonnet)

Uses the Agentrics Python SDK (agent_cost_optimizer) to wrap mock AI clients.
No real OpenAI/Anthropic API keys are needed — the mock clients return realistic
token counts so the SDK can track costs exactly as it would in production.
"""

import os
import random
import time
from dotenv import load_dotenv
from agent_cost_optimizer import Agentrics

load_dotenv()

API_KEY = os.environ.get("AGENTRICS_API_KEY")

if not API_KEY:
    raise SystemExit("Error: AGENTRICS_API_KEY not set. Copy .env.example to .env and add your key.")

# --- Mock AI clients ---
# These mimic the response shape that the SDK reads from real OpenAI/Anthropic clients.
# Swap them out for real clients (openai.OpenAI(), anthropic.Anthropic()) in production.

class _MockOpenAIUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

class _MockOpenAIResponse:
    def __init__(self, prompt_tokens: int, completion_tokens: int):
        self.usage = _MockOpenAIUsage(prompt_tokens, completion_tokens)

class _MockOpenAICompletions:
    def __init__(self, input_range: tuple, output_range: tuple, latency_range: tuple):
        self._input_range = input_range
        self._output_range = output_range
        self._latency_range = latency_range

    def create(self, **kwargs):
        latency_ms = random.randint(*self._latency_range)
        time.sleep(latency_ms / 5000)  # scaled down for demo speed
        return _MockOpenAIResponse(
            prompt_tokens=random.randint(*self._input_range),
            completion_tokens=random.randint(*self._output_range),
        )

class _MockOpenAIChat:
    def __init__(self, input_range, output_range, latency_range):
        self.completions = _MockOpenAICompletions(input_range, output_range, latency_range)

class MockOpenAI:
    """Drop-in mock for openai.OpenAI(). Returns realistic token counts without API calls."""
    def __init__(self, input_range: tuple, output_range: tuple, latency_range: tuple):
        self.chat = _MockOpenAIChat(input_range, output_range, latency_range)


class _MockAnthropicUsage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

class _MockAnthropicResponse:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.usage = _MockAnthropicUsage(input_tokens, output_tokens)

class _MockAnthropicMessages:
    def __init__(self, input_range: tuple, output_range: tuple, latency_range: tuple):
        self._input_range = input_range
        self._output_range = output_range
        self._latency_range = latency_range

    def create(self, **kwargs):
        latency_ms = random.randint(*self._latency_range)
        time.sleep(latency_ms / 5000)
        return _MockAnthropicResponse(
            input_tokens=random.randint(*self._input_range),
            output_tokens=random.randint(*self._output_range),
        )

class MockAnthropic:
    """Drop-in mock for anthropic.Anthropic(). Returns realistic token counts without API calls."""
    def __init__(self, input_range: tuple, output_range: tuple, latency_range: tuple):
        self.messages = _MockAnthropicMessages(input_range, output_range, latency_range)


# --- Pipeline setup ---

agentrics = Agentrics(api_key=API_KEY)

# Each agent wraps a mock client via the SDK — identical to how a real integration works.
# Agent names are prefixed with "demo:" so they can be identified and cleared
# from the dashboard with the "Clear demo data" button.
classifier = agentrics.wrap_anthropic(
    MockAnthropic(input_range=(200, 500), output_range=(50, 150), latency_range=(300, 800)),
    agent_id="demo:classifier-agent",
    agent_name="demo:classifier-agent",
)
researcher = agentrics.wrap_openai(
    MockOpenAI(input_range=(500, 1500), output_range=(200, 600), latency_range=(600, 1500)),
    agent_id="demo:research-agent",
    agent_name="demo:research-agent",
)
writer = agentrics.wrap_anthropic(
    MockAnthropic(input_range=(800, 2000), output_range=(300, 800), latency_range=(1000, 2500)),
    agent_id="demo:response-writer",
    agent_name="demo:response-writer",
)

SAMPLE_TICKETS = [
    "My order hasn't arrived and it's been 2 weeks.",
    "I was charged twice for my subscription this month.",
    "The app keeps crashing when I try to upload photos.",
    "I need to change my delivery address for an active order.",
    "How do I cancel my account and get a refund?",
    "My promo code isn't working at checkout.",
    "I received the wrong item in my shipment.",
    "The website is showing an error when I try to log in.",
]


def run_pipeline(ticket: str, run_num: int) -> None:
    print(f"\n  Run #{run_num}: \"{ticket[:60]}{'...' if len(ticket) > 60 else ''}\"")

    classifier.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=256,
        messages=[{"role": "user", "content": f"Classify this support ticket: {ticket}"}],
    )
    print("    [demo:classifier-agent]  done")

    researcher.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Find relevant policies for: {ticket}"}],
    )
    print("    [demo:research-agent]    done")

    writer.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[{"role": "user", "content": f"Draft a reply for: {ticket}"}],
    )
    print("    [demo:response-writer]   done")


def main():
    dashboard_url = (os.environ.get("AGENTRICS_BASE_URL") or "https://www.agentrics.io") + "/dashboard"
    print("Agentrics Demo — Customer Support Pipeline")
    print(f"Dashboard: {dashboard_url}")
    print()

    num_runs = random.randint(5, 8)
    tickets = random.choices(SAMPLE_TICKETS, k=num_runs)

    print(f"Running {num_runs} support tickets through the 3-agent pipeline...")

    for i, ticket in enumerate(tickets, 1):
        run_pipeline(ticket, i)

    print(f"\nDone! Check your dashboard to see cost breakdowns by agent.")
    print(f"  {dashboard_url}")


if __name__ == "__main__":
    main()
