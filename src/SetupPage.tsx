// First run: MarkItDown is not installed. tomd installs it into its own
// environment; nothing is bundled.
import { Check, X } from "lucide-react";
import { useState } from "react";
import type { Environment } from "./environment";
import { call } from "./ipc";
import { LogBox } from "./LogBox";
import { Button } from "./ui";

function Item({ ok, text }: { ok: boolean; text: string }) {
  const Icon = ok ? Check : X;
  return (
    <li className="flex items-center gap-2">
      <Icon size={14} className={ok ? "text-green" : "text-amber"} />
      <span className="truncate text-soft" title={text}>{text}</span>
    </li>
  );
}

export function SetupPage({ environment, onDone }: { environment: Environment; onDone: () => void }) {
  const [lines, setLines] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const run = async (method: "install_markitdown" | "install_homebrew_python") => {
    setBusy(true);
    setError("");
    setLines([]);
    try {
      await call(method, {}, (line) => setLines((all) => [...all, line]));
      onDone();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    } finally {
      setBusy(false);
    }
  };

  const { python, python_version, uv } = environment;
  return (
    <div className="flex h-full flex-col gap-4 overflow-auto p-6">
      <div>
        <h1 className="text-lg font-semibold">One-time setup</h1>
        <p className="mt-1 text-soft">
          tomd converts files with Microsoft MarkItDown. It is not installed yet; tomd can install
          it into its own private environment.
        </p>
      </div>
      <ul className="space-y-1.5 rounded-lg bg-panel p-3">
        <Item ok={!!python} text={python ? `Python ${python_version ?? ""} at ${python}` : "Python not found (tomd will fetch one)"} />
        <Item ok={!!uv} text={uv ? `uv at ${uv}` : "uv not found (tomd will download it)"} />
        <Item ok={false} text="MarkItDown not installed" />
      </ul>
      <div className="flex flex-wrap gap-2">
        <Button primary disabled={busy} onClick={() => run("install_markitdown")}>
          {busy ? "Installing…" : "Install MarkItDown"}
        </Button>
        <Button disabled={busy} title="Install Python with Homebrew, then MarkItDown"
          onClick={() => run("install_homebrew_python")}>
          Use Homebrew instead
        </Button>
      </div>
      {error && <p className="text-red select-text">{error}</p>}
      <LogBox lines={lines} />
    </div>
  );
}
