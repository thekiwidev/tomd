import { disable, enable, isEnabled } from "@tauri-apps/plugin-autostart";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import type { Environment, Foreign } from "./environment";
import { call } from "./ipc";
import { LogBox } from "./LogBox";
import { invoke } from "@tauri-apps/api/core";
import { type Anchor, type DragMode, type Settings, setSetting } from "./settings";
import { Button, Switch } from "./ui";

const ANCHORS: [Anchor, string][] = [
  ["top-left", "Top left"], ["top-right", "Top right"],
  ["left-center", "Left"], ["right-center", "Right"],
  ["bottom-left", "Bottom left"], ["bottom-right", "Bottom right"],
];

const DRAG_MODES: [DragMode, string][] = [
  ["show", "Show the drop zone"],
  ["shake", "Shake to hide"],
  ["small", "Start small"],
  ["option", "Hold Option to hide"],
];

function healthText(environment: Environment | null) {
  if (!environment) return "Checking…";
  const { markitdown, health } = environment;
  if (!markitdown) return "MarkItDown is not installed";
  if (!health) return "Checking…";
  if (health.ok) return `MarkItDown ${health.version_str} is working`;
  if (!health.version_ok) return `MarkItDown ${health.version_str ?? ""} is too old`;
  return `MarkItDown cannot convert: ${health.missing_features?.join(", ")}`;
}

type Props = {
  settings: Settings;
  environment: Environment | null;
  onRefresh: () => Promise<void>;
  onBack: () => void;
};

export function SettingsPage({ settings, environment, onRefresh, onBack }: Props) {
  const [loginItem, setLoginItem] = useState(false);
  const [finderAvailable, setFinderAvailable] = useState(true);
  const [foreign, setForeign] = useState<Foreign[]>([]);
  const [removeForeign, setRemoveForeign] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    isEnabled().then(setLoginItem, () => undefined);
    invoke<boolean>("quick_action_available").then(setFinderAvailable, () => undefined);
    call<Foreign[]>("find_foreign_markitdowns").then(setForeign, () => undefined);
  }, []);

  const repair = async () => {
    setBusy(true);
    setError("");
    setLines([]);
    try {
      await call("repair_markitdown",
        { deep_targets: removeForeign ? foreign.map((f) => f.interpreter) : [] },
        (line) => setLines((all) => [...all, line]));
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    }
    await onRefresh();
    setBusy(false);
  };

  const healthy = environment?.health?.ok;
  return (
    <div className="flex h-full flex-col overflow-auto p-5">
      <button type="button" onClick={onBack} className="mb-3 flex items-center gap-1.5 self-start text-soft hover:text-text">
        <ArrowLeft size={14} /> Back
      </button>
      <h1 className="mb-2 text-lg font-semibold">Settings</h1>

      <section className="divide-y divide-line rounded-lg bg-panel px-3">
        <Switch label="Drop zone" hint="A floating panel that appears while you drag a file"
          checked={settings.dropzone_enabled} onChange={(on) => setSetting("dropzone_enabled", on)} />
        <div className="py-2">
          <span className="block">Position</span>
          <div className="mt-1.5 grid grid-cols-2 gap-1.5">
            {ANCHORS.map(([anchor, label]) => (
              <button key={anchor} type="button" disabled={!settings.dropzone_enabled}
                onClick={() => setSetting("dock_anchor", anchor)}
                className={`rounded-md px-2 py-1.5 text-xs disabled:opacity-40 ${settings.dock_anchor === anchor
                  ? "bg-accent-strong text-white" : "bg-raised hover:bg-raised-hover"}`}>
                {label}
              </button>
            ))}
          </div>
        </div>
        <label className="flex items-center justify-between gap-4 py-2">
          <span>
            <span className="block">When a drag starts</span>
            <span className="block text-xs text-muted">How the drop zone gets out of the way of what is under it</span>
          </span>
          <select className="rounded-md border border-line bg-raised px-2 py-1 text-xs disabled:opacity-40"
            disabled={!settings.dropzone_enabled} value={settings.drag_mode}
            onChange={(e) => setSetting("drag_mode", e.target.value as DragMode)}>
            {DRAG_MODES.map(([mode, label]) => <option key={mode} value={mode}>{label}</option>)}
          </select>
        </label>
        <Switch label="Convert to Markdown in Finder"
          hint={finderAvailable
            ? "Right-click a file, Quick Actions, Convert to Markdown"
            : "Only from an installed tomd, not a development build"}
          checked={settings.finder_action} onChange={(on) => setSetting("finder_action", on)} />
        <Switch label="Auto-convert on drop" checked={settings.auto_convert_on_drop}
          onChange={(on) => setSetting("auto_convert_on_drop", on)} />
        <Switch label="Menu bar only" hint="Hide the Dock icon"
          checked={settings.menu_bar_only} onChange={(on) => setSetting("menu_bar_only", on)} />
        <Switch label="Start at login" checked={loginItem}
          onChange={async (on) => {
            await (on ? enable() : disable()).catch(() => undefined);
            setLoginItem(await isEnabled());
          }} />
      </section>

      <h2 className="mb-1.5 mt-5 font-medium">MarkItDown</h2>
      <section className="space-y-2.5 rounded-lg bg-panel p-3">
        <p className={healthy === false ? "text-amber" : "text-soft"}>{healthText(environment)}</p>
        {environment?.markitdown && (
          <p className="truncate text-xs text-muted select-text" title={environment.markitdown}>
            using {environment.markitdown}
          </p>
        )}
        {foreign.length > 0 && (
          <label className="flex items-center gap-2 text-xs text-soft">
            <input type="checkbox" className="accent-accent" checked={removeForeign}
              onChange={(e) => setRemoveForeign(e.target.checked)} />
            Also remove {foreign.length} other MarkItDown install{foreign.length > 1 ? "s" : ""} on this Mac
          </label>
        )}
        <Button disabled={busy} onClick={repair}>{busy ? "Repairing…" : "Repair MarkItDown"}</Button>
        {error && <p className="text-red select-text">{error}</p>}
        <LogBox lines={lines} />
      </section>
      <p className="mt-3 text-xs text-muted">Changes apply immediately.</p>
    </div>
  );
}
