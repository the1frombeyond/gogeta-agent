import { multiPick } from "./multi_pick.js";
import { WhatsAppConnector } from "./connectors/whatsapp.js";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";
import * as readline from "node:readline";
import { stdin, stdout } from "node:process";

const GOGETA_HOME = path.join(os.homedir(), ".gogeta");
const CONFIG_PATH = path.join(GOGETA_HOME, "config.yaml");

interface SetupConfig {
  provider: string;
  messengers: string[];
  features: string[];
  lifeline: string;
}

const PROVIDERS = [
  "Nous Portal",
  "OpenRouter",
  "Anthropic Claude",
  "OpenAI",
  "Google Gemini",
  "DeepSeek",
  "NVIDIA NIM",
  "LM Studio",
  "Ollama",
  "AWS Bedrock",
  "Azure OpenAI",
  "Custom",
];

const PROVIDER_DESCS = [
  "Everything your agent needs, 300+ models with bundled tool use",
  "Pay-per-use API aggregator",
  "Claude models via API key",
  "GPT models via API key",
  "Gemini models via AI Studio API",
  "V3, R1, coder models",
  "Nemotron models via build.nvidia.com",
  "Local desktop app with built-in model server",
  "Cloud-hosted open models",
  "Claude, Nova, Llama, DeepSeek via AWS",
  "OpenAI or Anthropic endpoint on Azure",
  "Direct API endpoint (enter URL manually)",
];

const MESSENGERS = [
  "Telegram",
  "Discord",
  "Slack",
  "WhatsApp Web",
  "Signal",
  "Matrix",
  "Mattermost",
  "Email (SMTP/IMAP)",
  "SMS (Twilio)",
  "WeChat",
  "DingTalk",
  "Feishu / Lark",
  "QQ Bot",
  "Webhook",
  "API Server",
];

const MESSENGER_DESCS = [
  "Bot API with polling + webhook support",
  "Bot with slash commands and thread management",
  "Slash commands via Socket Mode",
  "Playwright-based QR auth with persistent sessions",
  "Signal CLI REST API bridge",
  "Matrix protocol with E2E support",
  "Mattermost webhook + API integration",
  "Send and receive via SMTP/IMAP",
  "Two-way SMS via Twilio API",
  "WeChat contact/platform integration",
  "DingTalk bot with outgoing webhook",
  "Feishu bot with card messages",
  "QQ channel bot via Tencent API",
  "Receive incoming webhooks from any service",
  "REST API for custom integrations",
];

const FEATURES = [
  "Web Search",
  "File System",
  "Code Execution",
  "Vision & Images",
  "Memory",
  "Web Browsing",
  "Voice / TTS",
  "Cron Jobs",
  "Delegation",
  "Git Integration",
  "Knowledge Base",
  "Plugin System",
];

const FEATURE_DESCS = [
  "Search the web for real-time information",
  "Read, write, and manage files",
  "Run Python, Node, shell, and compiled code",
  "Analyze images and generate visuals",
  "Persist context across sessions",
  "Interactive browser automation",
  "Text-to-speech and speech-to-text",
  "Schedule recurring agent tasks",
  "Spawn sub-agents for parallel work",
  "Commit, diff, and manage repos",
  "Load custom skills and reference docs",
  "Extend with community plugins",
];

function promptForAPIKey(name: string, url: string): Promise<string | null> {
  stdout.write(`\n\x1b[1m${name} API Key\x1b[22m\n`);
  stdout.write(`  Get one at: \x1b[4m${url}\x1b[24m\n`);
  stdout.write(`  Enter key (or leave empty to skip): `);

  const rl = readline.createInterface({ input: stdin, output: stdout });
  return new Promise((resolve) => {
    rl.question("", (answer) => {
      rl.close();
      resolve(answer.trim() || null);
    });
  });
}

function promptFreeform(promptText: string, def?: string): Promise<string> {
  const defaultStr = def ? ` [${def}]` : "";
  stdout.write(`\n\x1b[1m${promptText}\x1b[22m${defaultStr}: `);

  const rl = readline.createInterface({ input: stdin, output: stdout });
  return new Promise((resolve) => {
    rl.question("", (answer) => {
      rl.close();
      resolve(answer.trim() || def || "");
    });
  });
}

export async function runSetupWizard(): Promise<SetupConfig> {
  stdout.write("\x1b[2J\x1b[H");
  stdout.write(`
\x1b[33m┌──────────────────────────────────────────────────────┐\x1b[39m
\x1b[33m│           \x1b[1mGogeta Agent Setup Wizard\x1b[22m                │\x1b[39m
\x1b[33m├──────────────────────────────────────────────────────┤\x1b[39m
\x1b[33m│  Let's configure your Gogeta Agent installation.     │\x1b[39m
\x1b[33m│  Press Ctrl+C at any time to exit.                    │\x1b[39m
\x1b[33m└──────────────────────────────────────────────────────┘\x1b[39m

`);

  await sleep(800);

  stdout.write(`\x1b[1m\x1b[2mStep 1/4\x1b[22m — Inference Provider\x1b[22m\n\n`);
  const providerResult = await multiPick(PROVIDERS, {
    prompt: "Choose your primary inference provider:",
    descriptions: PROVIDER_DESCS,
    selectAll: false,
  });

  const providerIdx = providerResult.size > 0 ? [...providerResult][0] : 0;
  const provider = PROVIDERS[providerIdx];

  if (provider !== "LM Studio" && provider !== "Ollama") {
    const keyUrl = getProviderKeyUrl(provider);
    const key = await promptForAPIKey(provider, keyUrl);
    if (key) {
      const apiKeyPath = path.join(GOGETA_HOME, ".env");
      const envEntry = `${getProviderEnvVar(provider)}="${key}"`;
      if (fs.existsSync(apiKeyPath)) {
        fs.appendFileSync(apiKeyPath, `\n${envEntry}\n`);
      } else {
        fs.mkdirSync(path.dirname(apiKeyPath), { recursive: true });
        fs.writeFileSync(apiKeyPath, `${envEntry}\n`);
      }
    }
  }

  if (!fs.existsSync(GOGETA_HOME)) {
    fs.mkdirSync(GOGETA_HOME, { recursive: true });
  }

  stdout.write(`\n\x1b[1m\x1b[2mStep 2/4\x1b[22m — Messaging Platforms\x1b[22m\n\n`);
  stdout.write(`  Choose which messaging platforms to enable.\n`);
  stdout.write(`  You'll configure credentials for each one.\n\n`);

  const messengerResult = await multiPick(MESSENGERS, {
    prompt: "Select messaging platforms:",
    descriptions: MESSENGER_DESCS,
    selectAll: true,
  });

  const messengers = [...messengerResult].map((i) => MESSENGERS[i]);

  for (const m of messengers) {
    if (m === "WhatsApp Web") {
      const setupWw = await promptYesNo("\nSet up WhatsApp Web now?");
      if (setupWw) {
        try {
          const ww = new WhatsAppConnector(GOGETA_HOME);
          await ww.connect();
        } catch (e: any) {
          stdout.write(`  \x1b[31mWhatsApp setup failed: ${e.message}\x1b[39m\n`);
        }
      }
    } else {
      const keyUrl = getMessengerKeyUrl(m);
      await promptForAPIKey(m, keyUrl);
    }
  }

  stdout.write(`\n\x1b[1m\x1b[2mStep 3/4\x1b[22m — Features\x1b[22m\n\n`);
  stdout.write(`  Toggle which capabilities your agent should have.\n\n`);

  const featureResult = await multiPick(FEATURES, {
    prompt: "Select features to enable:",
    descriptions: FEATURE_DESCS,
    selectAll: true,
  });

  const features = [...featureResult].map((i) => FEATURES[i]);

  stdout.write(`\n\x1b[1m\x1b[2mStep 4/4\x1b[22m — Lifeline (Emergency Contact)\x1b[22m\n\n`);
  stdout.write(`  If something goes wrong, who should the agent contact?\n\n`);

  const lifelinePhone = await promptFreeform(
    "Emergency phone (SMS)",
    "",
  );
  const lifelineEmail = await promptFreeform(
    "Emergency email",
    "",
  );

  const config: SetupConfig = {
    provider,
    messengers,
    features,
    lifeline: lifelinePhone || lifelineEmail || "none",
  };

  saveConfig(config);
  stdout.write(`\n\x1b[32m✓ Setup complete!\x1b[39m\n`);
  stdout.write(`  Config saved to: \x1b[2m${CONFIG_PATH}\x1b[22m\n`);
  stdout.write(`  API keys saved to: \x1b[2m${path.join(GOGETA_HOME, ".env")}\x1b[22m\n\n`);

  return config;
}

function saveConfig(config: SetupConfig): void {
  const yaml = [
    "# Gogeta Agent Configuration",
    `# Generated by setup wizard`,
    "",
    "provider:",
    `  name: "${config.provider}"`,
    "",
    "messengers:",
    ...config.messengers.map((m) => `  - "${m}"`),
    "",
    "features:",
    ...config.features.map((f) => `  - "${f.toLowerCase().replace(/\s+/g, "_")}"`),
    "",
    `lifeline: "${config.lifeline}"`,
    "",
  ].join("\n");

  fs.mkdirSync(path.dirname(CONFIG_PATH), { recursive: true });
  fs.writeFileSync(CONFIG_PATH, yaml, "utf-8");
}

function getProviderKeyUrl(provider: string): string {
  const urls: Record<string, string> = {
    "Nous Portal": "https://portal.nousresearch.com",
    "OpenRouter": "https://openrouter.ai/keys",
    "Anthropic Claude": "https://console.anthropic.com/",
    "OpenAI": "https://platform.openai.com/api-keys",
    "Google Gemini": "https://aistudio.google.com/",
    "DeepSeek": "https://platform.deepseek.com/api_keys",
    "NVIDIA NIM": "https://build.nvidia.com/",
    "AWS Bedrock": "https://aws.amazon.com/bedrock/",
    "Azure OpenAI": "https://portal.azure.com/",
    "Custom": "https://your-api-endpoint/",
  };
  return urls[provider] ?? "https://console";
}

function getProviderEnvVar(provider: string): string {
  const vars: Record<string, string> = {
    "Nous Portal": "NOUS_API_KEY",
    "OpenRouter": "OPENROUTER_API_KEY",
    "Anthropic Claude": "ANTHROPIC_API_KEY",
    "OpenAI": "OPENAI_API_KEY",
    "Google Gemini": "GEMINI_API_KEY",
    "DeepSeek": "DEEPSEEK_API_KEY",
    "NVIDIA NIM": "NVIDIA_API_KEY",
    "AWS Bedrock": "AWS_ACCESS_KEY_ID",
    "Azure OpenAI": "AZURE_OPENAI_KEY",
    "Custom": "CUSTOM_API_KEY",
  };
  return vars[provider] ?? "API_KEY";
}

function getMessengerKeyUrl(messenger: string): string {
  const urls: Record<string, string> = {
    "Telegram": "https://t.me/BotFather",
    "Discord": "https://discord.com/developers/applications",
    "Slack": "https://api.slack.com/apps",
    "Signal": "https://signal.org/download/",
    "Matrix": "https://matrix.org/docs/guides/",
    "Mattermost": "https://mattermost.com/integrations/",
    "Email (SMTP/IMAP)": "https://support.google.com/mail/answer/185833",
    "SMS (Twilio)": "https://console.twilio.com/",
    "WeChat": "https://open.weixin.qq.com/",
    "DingTalk": "https://open.dingtalk.com/",
    "Feishu / Lark": "https://open.feishu.cn/",
    "QQ Bot": "https://bot.q.qq.com/",
    "Webhook": "https://webhook.site/",
    "API Server": "http://localhost:8080/docs",
  };
  return urls[messenger] ?? "https://console";
}

function promptYesNo(question: string): Promise<boolean> {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: stdin, output: stdout });
    rl.question(`\x1b[1m${question}\x1b[22m (Y/n): `, (answer) => {
      rl.close();
      resolve(answer.trim().toLowerCase() !== "n");
    });
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
