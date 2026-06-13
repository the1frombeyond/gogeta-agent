import { runSetupWizard } from "./wizard.js";
import { stdin, stdout } from "node:process";

function showHelp(): void {
  stdout.write(`
\x1b[1mGogeta Setup — Interactive Configuration Wizard\x1b[22m

Usage: gogeta setup [options]

Options:
  --help, -h     Show this help message
  --non-interactive  Use defaults/env vars (not yet implemented)
  --quick        Only prompt for missing/unset items (not yet implemented)

Sections:
  This wizard walks you through 4 steps:
    1. Choose an inference provider
    2. Configure messaging platforms
    3. Toggle agent features
    4. Set emergency lifeline

`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.includes("-h")) {
    showHelp();
    process.exit(0);
  }

  try {
    await runSetupWizard();
  } catch (e: any) {
    if (e.message === "Interrupted") {
      stdout.write("\n\x1b[33mSetup cancelled.\x1b[39m\n");
      process.exit(130);
    }
    stdout.write(`\n\x1b[31mSetup failed: ${e.message}\x1b[39m\n`);
    process.exit(1);
  }
}

main();
