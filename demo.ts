/**
 * Agentrics Demo — Customer Support Pipeline (TypeScript)
 *
 * Simulates a 3-agent pipeline that a customer might run:
 *   1. Classifier Agent  — reads a ticket, classifies urgency/category  (Claude Haiku 4.5)
 *   2. Research Agent    — looks up relevant info based on classification (GPT-4o mini)
 *   3. Response Writer   — drafts a customer-facing reply                (Claude Sonnet 4.6)
 *
 * Uses the Agentrics JS SDK (@agentrics/sdk) to wrap mock AI clients.
 * No real OpenAI/Anthropic API keys are needed — the mock clients return realistic
 * token counts so the SDK can track costs exactly as it would in production.
 */

import "dotenv/config";
import { Agentrics } from "@agentrics/sdk";

const API_KEY = process.env.AGENTRICS_API_KEY;
if (!API_KEY) {
  console.error("Error: AGENTRICS_API_KEY not set. Copy .env.example to .env and add your key.");
  process.exit(1);
}

// --- Mock AI clients ---
// These mimic the response shape that the SDK reads from real OpenAI/Anthropic clients.
// Swap them out for real clients (new OpenAI(), new Anthropic()) in production.

function randInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

interface MockClientOptions {
  model: string;
  inputRange: [number, number];
  outputRange: [number, number];
  latencyRange: [number, number];
}

class MockOpenAI {
  /** Drop-in mock for new OpenAI(). Returns realistic token counts without API calls. */
  readonly model: string;
  readonly chat: {
    completions: {
      create: (params: Record<string, unknown>) => Promise<{ usage: { prompt_tokens: number; completion_tokens: number } }>;
    };
  };

  constructor({ model, inputRange, outputRange, latencyRange }: MockClientOptions) {
    this.model = model;
    this.chat = {
      completions: {
        create: async (_params: Record<string, unknown>) => {
          await sleep(randInt(...latencyRange) / 5); // scaled down for demo speed
          return {
            usage: {
              prompt_tokens: randInt(...inputRange),
              completion_tokens: randInt(...outputRange),
            },
          };
        },
      },
    };
  }
}

class MockAnthropic {
  /** Drop-in mock for new Anthropic(). Returns realistic token counts without API calls. */
  readonly model: string;
  readonly messages: {
    create: (params: Record<string, unknown>) => Promise<{ usage: { input_tokens: number; output_tokens: number } }>;
  };

  constructor({ model, inputRange, outputRange, latencyRange }: MockClientOptions) {
    this.model = model;
    this.messages = {
      create: async (_params: Record<string, unknown>) => {
        await sleep(randInt(...latencyRange) / 5);
        return {
          usage: {
            input_tokens: randInt(...inputRange),
            output_tokens: randInt(...outputRange),
          },
        };
      },
    };
  }
}

// --- Pipeline setup ---

const BASE_URL = process.env.AGENTRICS_BASE_URL ?? "https://www.agentrics.io";
const optimizer = new Agentrics({ apiKey: API_KEY });

// Each agent wraps a mock client via the SDK — identical to how a real integration works.
// Agent names are prefixed with "js:" so they can be distinguished from the Python demo
// agents and cleared from the dashboard with the "Clear demo data" button.
const classifier = optimizer.wrapAnthropic(
  new MockAnthropic({
    model: "claude-haiku-4-5-20251001",
    inputRange: [8_000, 20_000],
    outputRange: [200, 800],
    latencyRange: [300, 800],
  }),
  "js:classifier-agent",
  "js:classifier-agent"
);

const researcher = optimizer.wrapOpenAI(
  new MockOpenAI({
    model: "gpt-4o-mini",
    inputRange: [30_000, 80_000],
    outputRange: [1_000, 4_000],
    latencyRange: [600, 1500],
  }),
  "js:research-agent",
  "js:research-agent"
);

const writer = optimizer.wrapAnthropic(
  new MockAnthropic({
    model: "claude-sonnet-4-6",
    inputRange: [8_000, 25_000],
    outputRange: [400, 1_500],
    latencyRange: [1000, 2500],
  }),
  "js:response-writer",
  "js:response-writer"
);

const SAMPLE_TICKETS = [
  "My order hasn't arrived and it's been 2 weeks.",
  "I was charged twice for my subscription this month.",
  "The app keeps crashing when I try to upload photos.",
  "I need to change my delivery address for an active order.",
  "How do I cancel my account and get a refund?",
  "My promo code isn't working at checkout.",
  "I received the wrong item in my shipment.",
  "The website is showing an error when I try to log in.",
];

async function runPipeline(ticket: string, runNum: number): Promise<void> {
  const preview = ticket.length > 60 ? ticket.slice(0, 60) + "..." : ticket;
  console.log(`\n  Run #${runNum}: "${preview}"`);

  await classifier.messages.create({
    model: classifier.model,
    max_tokens: 256,
    messages: [{ role: "user", content: `Classify this support ticket: ${ticket}` }],
  });
  console.log("    [js:classifier-agent]  done");

  await researcher.chat.completions.create({
    model: researcher.model,
    messages: [{ role: "user", content: `Find relevant policies for: ${ticket}` }],
  });
  console.log("    [js:research-agent]    done");

  await writer.messages.create({
    model: writer.model,
    max_tokens: 512,
    messages: [{ role: "user", content: `Draft a reply for: ${ticket}` }],
  });
  console.log("    [js:response-writer]   done");
}

async function main(): Promise<void> {
  const dashboardUrl = `${BASE_URL}/dashboard`;
  console.log("Agentrics Demo — Customer Support Pipeline (TS)");
  console.log(`Dashboard: ${dashboardUrl}`);
  console.log();

  const numRuns = randInt(25, 40);
  const tickets = Array.from(
    { length: numRuns },
    () => SAMPLE_TICKETS[Math.floor(Math.random() * SAMPLE_TICKETS.length)]
  );

  console.log(`Running ${numRuns} support tickets through the 3-agent pipeline...`);

  for (let i = 0; i < tickets.length; i++) {
    await runPipeline(tickets[i], i + 1);
  }

  console.log(`\nDone! Check your dashboard to see cost breakdowns by agent.`);
  console.log(`  ${dashboardUrl}`);
}

main();
