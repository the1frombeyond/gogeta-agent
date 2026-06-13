import * as fs from "node:fs";
import * as path from "node:path";
import { chromium, type BrowserContext, type Page } from "playwright";

const QR_TIMEOUT_MS = 120_000;
const QR_POLL_INTERVAL_MS = 2_000;
const STORAGE_REL = "sessions/whatsapp/storage_state.json";
const META_REL = "sessions/whatsapp/meta.json";

interface EventHandler {
  (event: string, data: unknown): void;
}

class EventRouter {
  private handlers: Map<string, EventHandler[]> = new Map();
  private history: Array<{ event: string; data: unknown; ts: number }> = [];
  private maxHistory = 100;

  on(event: string, handler: EventHandler): void {
    const list = this.handlers.get(event) ?? [];
    list.push(handler);
    this.handlers.set(event, list);
  }

  off(event: string, handler: EventHandler): void {
    const list = this.handlers.get(event) ?? [];
    this.handlers.set(
      event,
      list.filter((h) => h !== handler),
    );
  }

  emit(event: string, data: unknown): void {
    const entry = { event, data, ts: Date.now() };
    this.history.push(entry);
    if (this.history.length > this.maxHistory) this.history.shift();

    for (const handler of this.handlers.get(event) ?? []) {
      try {
        handler(event, data);
      } catch { /* ignore handler errors */ }
    }
  }

  replay(event: string, handler: EventHandler): void {
    for (const entry of this.history) {
      if (entry.event === event) handler(entry.event, entry.data);
    }
  }
}

interface Message {
  from: string;
  body: string;
  timestamp: number;
  chatId: string;
}

type SlashHandler = (cmd: string, args: string[], msg: Message) => Promise<string | void>;

class MessageHandler {
  private slashCommands: Map<string, SlashHandler> = new Map();

  register(cmd: string, handler: SlashHandler): void {
    this.slashCommands.set(cmd.toLowerCase(), handler);
  }

  async handle(msg: Message): Promise<string | void> {
    const text = msg.body.trim();
    if (!text.startsWith("/")) return;

    const parts = text.slice(1).split(/\s+/);
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);

    const handler = this.slashCommands.get(cmd);
    if (handler) {
      return handler(cmd, args, msg);
    }
  }
}

class SessionManager {
  private dataDir: string;

  constructor(baseDir: string) {
    this.dataDir = path.join(baseDir, STORAGE_REL);
  }

  get storagePath(): string {
    return this.dataDir;
  }

  get metaPath(): string {
    return path.join(path.dirname(this.dataDir), META_REL);
  }

  hasSession(): boolean {
    return fs.existsSync(this.storagePath);
  }

  saveStorage(state: { cookies: unknown[]; origins: unknown[] }): void {
    fs.mkdirSync(path.dirname(this.storagePath), { recursive: true });
    fs.writeFileSync(this.storagePath, JSON.stringify(state, null, 2), "utf-8");
  }

  loadStorage(): { cookies: unknown[]; origins: unknown[] } | null {
    if (!this.hasSession()) return null;
    return JSON.parse(fs.readFileSync(this.storagePath, "utf-8"));
  }

  saveMeta(meta: Record<string, unknown>): void {
    fs.mkdirSync(path.dirname(this.metaPath), { recursive: true });
    fs.writeFileSync(this.metaPath, JSON.stringify(meta, null, 2), "utf-8");
  }

  loadMeta(): Record<string, unknown> | null {
    if (!fs.existsSync(this.metaPath)) return null;
    return JSON.parse(fs.readFileSync(this.metaPath, "utf-8"));
  }
}

export class WhatsAppConnector {
  private baseDir: string;
  private events: EventRouter;
  private messages: MessageHandler;
  private sessions: SessionManager;
  private context: BrowserContext | null = null;
  private page: Page | null = null;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
    this.events = new EventRouter();
    this.messages = new MessageHandler();
    this.sessions = new SessionManager(baseDir);
  }

  get eventRouter(): EventRouter {
    return this.events;
  }

  get messageHandler(): MessageHandler {
    return this.messages;
  }

  get sessionManager(): SessionManager {
    return this.sessions;
  }

  async connect(): Promise<void> {
    if (this.sessions.hasSession()) {
      process.stdout.write("  \x1b[2mLoading existing WhatsApp session...\x1b[22m\n");
      const state = this.sessions.loadStorage()!;
      this.context = await chromium.launchPersistentContext("", {
        headless: false,
        storageState: state,
      } as any);
      this.page = this.context.pages()[0] || (await this.context.newPage());

      try {
        await this.page.goto("https://web.whatsapp.com", {
          waitUntil: "domcontentloaded",
          timeout: 30_000,
        });
        process.stdout.write("  \x1b[32mSession restored.\x1b[39m\n");
      } catch {
        process.stdout.write("  \x1b[33mSession expired, re-authenticating...\x1b[39m\n");
        await this.doQrAuth();
      }
    } else {
      await this.doQrAuth();
    }

    this.sessions.saveMeta({
      lastConnected: new Date().toISOString(),
      storagePath: this.sessions.storagePath,
    });
  }

  private async doQrAuth(): Promise<void> {
    if (this.context) await this.context.close().catch(() => {});
    if (this.page) await this.page.close().catch(() => {});

    process.stdout.write("  \x1b[1mLaunching WhatsApp Web...\x1b[22m\n");

    this.context = await chromium.launchPersistentContext("", {
      headless: false,
      args: ["--window-size=800,700"],
    });
    this.page = this.context.pages()[0] || (await this.context.newPage());
    await this.page.goto("https://web.whatsapp.com", {
      waitUntil: "domcontentloaded",
    });

    process.stdout.write("  \x1b[33mWaiting for QR code...\x1b[39m\n");

    const startTime = Date.now();
    let qrFound = false;

    while (Date.now() - startTime < QR_TIMEOUT_MS) {
      try {
        const qrCanvas = await this.page.$('canvas[aria-label="Scan me!"]');
        if (qrCanvas) {
          qrFound = true;
          const dataRef = await qrCanvas.evaluate((el) => el.getAttribute("data-ref"));
          if (dataRef) {
            process.stdout.write(
              `  \x1b[36mQR Code detected!\x1b[39m\n  Scan with WhatsApp: \x1b[4mhttps://web.whatsapp.com\x1b[24m\n`,
            );
          }
        }

        const currentUrl = this.page.url();
        if (qrFound && !currentUrl.includes("whatsapp.com")) {
          process.stdout.write("  \x1b[32mAuthentication successful!\x1b[39m\n");
          break;
        }

        if (qrFound) {
          const hasChat = await this.page.$("#pane-side, .two");
          if (hasChat) {
            process.stdout.write("  \x1b[32mWhatsApp Web authenticated!\x1b[39m\n");
            break;
          }
        }
      } catch { /* page may be navigating */ }

      await sleep(QR_POLL_INTERVAL_MS);
    }

    if (!qrFound) {
      process.stdout.write("  \x1b[31mQR code not found within timeout.\x1b[39m\n");
      return;
    }

    const state = await this.context.storageState();
    this.sessions.saveStorage(state as any);
    process.stdout.write(`  \x1b[2mSession saved to ${this.sessions.storagePath}\x1b[22m\n`);
  }

  async disconnect(): Promise<void> {
    if (this.context) {
      const state = await this.context.storageState();
      this.sessions.saveStorage(state as any);
      await this.context.close().catch(() => {});
    }
    this.context = null;
    this.page = null;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
