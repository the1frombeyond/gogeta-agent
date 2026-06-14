import { runSetupWizard } from "./wizard.js";
import { stdin, stdout } from "node:process";

async function main(): Promise<void> {
  try {
    await runSetupWizard();
  } catch (e: any) {
    if (e.message === "Interrupted") {
      stdout.write("\n\x1b[38;2;255;185;15mSetup cancelled.\x1b[0m\n");
      process.exit(130);
    }
    stdout.write(`\n\x1b[31mSetup failed: ${e.message}\x1b[0m\n`);
    process.exit(1);
  }
}

main();
