import { stdin as _stdin, stdout as _stdout } from "node:process";

export interface MultiPickOptions {
  prompt?: string;
  descriptions?: string[];
  preselect?: Set<number>;
  selectAll?: boolean;
}

const GOLD = "\x1b[38;2;255;185;15m";
const CYAN = "\x1b[38;2;0;200;255m";
const GREEN = "\x1b[38;2;80;220;100m";
const DIM = "\x1b[2m";
const BOLD = "\x1b[1m";
const RESET = "\x1b[22m\x1b[39m";

export async function multiPick(
  options: string[],
  opts: MultiPickOptions = {},
): Promise<Set<number>> {
  const { prompt = "Select", descriptions = [], selectAll = true, preselect } = opts;

  const isSingle = !selectAll;

  const hasSelectAll = selectAll && options.length > 1;
  const displayLabels = hasSelectAll
    ? ["[ Select All ]", ...options]
    : [...options];
  const displayDescs = hasSelectAll
    ? ["(toggle all items)", ...descriptions]
    : [...descriptions];

  const realCount = options.length;
  const displayCount = displayLabels.length;
  const selected = new Set<number>();

  if (isSingle) {
    selected.add(0);
  } else if (preselect) {
    for (const i of preselect) {
      if (i >= 0 && i < realCount) selected.add(i + (hasSelectAll ? 1 : 0));
    }
  }

  let cursor = 0;

  function restoreStdin(): void {
    try {
      if (_stdin.isRaw) _stdin.setRawMode(false);
    } catch { /* ignore */ }
    _stdin.removeAllListeners("data");
    _stdin.removeAllListeners("error");
  }

  function render(): void {
    const lines: string[] = [];

    for (let i = 0; i < displayCount; i++) {
      const isCursor = i === cursor;
      const mark = selected.has(i) ? `${GREEN}◆${RESET}` : `${DIM}◇${RESET}`;
      const label = displayLabels[i];
      const desc = displayDescs[i] ?? "";
      const prefix = isCursor ? `${GOLD}❯${RESET}` : " ";
      lines.push(`${prefix} ${mark} ${BOLD}${label}${RESET}  ${DIM}${desc}${RESET}`);
    }

    const count = (() => {
      let c = 0;
      for (const idx of selected) {
        if (hasSelectAll && idx === 0) continue;
        c++;
      }
      return c;
    })();
    const total = realCount;
    const hint = isSingle
      ? `${DIM}↑/↓ navigate · ${GOLD}Space${RESET}${DIM} select · ${GOLD}Enter${RESET}${DIM} confirm${RESET}`
      : `${DIM}↑/↓ navigate · ${GOLD}Space${RESET}${DIM} toggle · ${GOLD}Enter${RESET}${DIM} confirm · ${CYAN}a${RESET}${DIM} all/none — ${count}/${total} selected${RESET}`;

    _stdout.write("\x1b[2J\x1b[H");
    _stdout.write(`\x1b[1m${prompt}\x1b[22m\n\n`);
    _stdout.write(lines.join("\n"));
    _stdout.write(`\n\n${hint}\n`);
  }

  function toggleAll(): void {
    if (!isSingle) {
      const allSelected = selected.size === displayCount;
      if (allSelected) {
        for (let i = 0; i < displayCount; i++) selected.delete(i);
      } else {
        for (let i = 0; i < displayCount; i++) selected.add(i);
      }
    }
  }

  function toggleItem(idx: number): void {
    if (isSingle) {
      selected.clear();
      selected.add(idx);
      return;
    }
    if (hasSelectAll && idx === 0) {
      toggleAll();
      return;
    }
    if (selected.has(idx)) {
      selected.delete(idx);
    } else {
      selected.add(idx);
    }
    if (hasSelectAll) {
      const realSelected = Array.from(selected).filter((i) => i > 0).length;
      if (realSelected === realCount) {
        selected.add(0);
      } else {
        selected.delete(0);
      }
    }
  }

  return new Promise<Set<number>>((resolve, reject) => {
    try {
      _stdin.setRawMode(true);
    } catch {
      reject(new Error("Cannot set raw mode. Run in an interactive terminal."));
      return;
    }
    _stdin.resume();
    render();

    let buf = Buffer.alloc(0);

    _stdin.on("data", (chunk: Buffer) => {
      buf = Buffer.concat([buf, chunk]);

      if (buf.length === 1) {
        const b = buf[0];
        buf = Buffer.alloc(0);

        if (b === 0x03) {
          restoreStdin();
          reject(new Error("Interrupted"));
          return;
        }
        if (b === 0x0d || b === 0x0a) {
          restoreStdin();
          const result = new Set<number>();
          for (const i of selected) {
            if (hasSelectAll && i === 0) continue;
            result.add(i - (hasSelectAll ? 1 : 0));
          }
          _stdout.write("\x1b[2J\x1b[H");
          resolve(result);
          return;
        }
        if (b === 0x20) {
          toggleItem(cursor);
          render();
          return;
        }
        if (b === 0x61 || b === 0x41) {
          toggleAll();
          render();
          return;
        }
        if (b === 0x6a || b === 0x42) {
          cursor = (cursor + 1) % displayCount;
          render();
          return;
        }
        if (b === 0x6b) {
          cursor = (cursor - 1 + displayCount) % displayCount;
          render();
          return;
        }
      }

      if (buf.length >= 3 && buf[0] === 0x1b && buf[1] === 0x5b) {
        const seq = buf[2];
        buf = Buffer.alloc(0);

        if (seq === 0x41) {
          cursor = (cursor - 1 + displayCount) % displayCount;
          render();
          return;
        }
        if (seq === 0x42) {
          cursor = (cursor + 1) % displayCount;
          render();
          return;
        }
        return;
      }

      buf = Buffer.alloc(0);
    });

    _stdin.on("error", (err) => {
      restoreStdin();
      reject(err);
    });
  });
}
