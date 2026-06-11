# Getting Started with GOGETA

A 15-minute walkthrough from install to your first real workflow.

---

## Install

Open a terminal and run:

```bash
curl -fsSL https://gogeta.ai/install.sh | bash
```

Windows (PowerShell):

```powershell
iex (irm https://gogeta.ai/install.ps1)
```

That's it. The installer grabs Python + uv if needed, clones the repo, and puts `gogeta` on your path.

Once it finishes:

```bash
gogeta
```

You'll see the banner and a chat prompt. Type something — anything. It works with no config out of the box (it'll use a free tier or prompt you for a key).

---

## Pick a model

GOGETA is provider-agnostic. You can use OpenAI, Anthropic, Google, OpenRouter, local models, or 200+ others.

```bash
gogeta model
```

This opens an interactive menu. Pick a provider, enter your API key if needed, and pick a model. Or skip the menu and set it inline:

```bash
gogeta model set openrouter:anthropic/claude-sonnet-4
```

You can switch mid-conversation too:

```
/model openai:gpt-4o
```

No restart needed.

---

## Your first conversation

```
Hello
```

GOGETA will respond. Try asking it to do something multi-step:

```
Find all Python files in this repo that don't have tests, and summarize the top 5 most complex ones
```

It'll use the terminal tool to search, the file tool to read, and the delegate tool to parallelize. Watch the tool feed stream in real time.

---

## Install a skill

Skills are procedural memory files — markdown docs that teach GOGETA how to do specific things.

```bash
gogeta skills list                     # See what's already installed
gogeta skills browse                   # Browse the Skills Hub
gogeta skills install official/github/pr-review
```

Once installed, you can invoke the skill during a conversation:

```
Run the pr-review skill on this PR
```

The agent reads the SKILL.md and follows its procedure steps. Skills auto-improve over time via the Curator background process.

---

## Schedule a job

```bash
/cron add "every day at 9am" "check the status of our production services and report any issues"
```

GOGETA will run that every day at 9am and deliver the result to whatever platform you're on — terminal, Telegram, email, etc.

---

## Set up the gateway

The gateway lets you talk to GOGETA from messaging platforms.

```bash
gogeta gateway setup
```

Follow the prompts to connect Telegram, Discord, Slack, WhatsApp, or any of the 15+ supported platforms. Then:

```bash
gogeta gateway run
```

Your agent is now reachable from those platforms. One daemon, all platforms.

---

## What's next

- `/help` — full list of slash commands
- `gogeta --tui` — launch the React terminal UI
- `gogeta dashboard` — browser-based dashboard
- `gogeta skills create` — write your own skill
- `gogeta plugin list` — check installed plugins
- [INSTALL.md](INSTALL.md) — detailed install options
- [gogeta.ai/docs](https://gogeta.ai/docs/) — full documentation
