import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWebview } from "@tauri-apps/api/webview";
import { open } from "@tauri-apps/plugin-dialog";
import { FolderOpen, Play, Plus, Settings as Cog, Square, Trash2, Video, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useEnvironment } from "./environment";
import { FileRow } from "./FileRow";
import { call } from "./ipc";
import { inFlight, toastOf } from "./queue";
import { SettingsPage } from "./SettingsPage";
import { SetupPage } from "./SetupPage";
import { useSettings } from "./settings";
import { baseName, Button, reveal } from "./ui";
import { useQueue } from "./useQueue";
import { YouTubeDialog } from "./YouTubeDialog";

export const SOURCES_DROPPED = "sources-dropped";
export const QUEUE_RUN = "queue-run";

export function MainWindow() {
  const settings = useSettings();
  const { environment, error, refresh } = useEnvironment();
  const [queue, dispatch] = useQueue(environment?.markitdown ?? null);
  const [view, setView] = useState<"list" | "settings">("list");
  const [youtube, setYoutube] = useState(false);
  const [over, setOver] = useState(false);
  const [toast, setToast] = useState("");

  // Listeners are registered once; they read the latest setting through a ref.
  const autoConvert = useRef(false);
  autoConvert.current = settings?.auto_convert_on_drop ?? false;

  const addPaths = useCallback(async (paths: string[], background = false) => {
    const files = await call<string[]>("collect_paths", { paths });
    if (!files.length) return setToast("Nothing convertible in that drop");
    dispatch({
      type: "add", enqueue: autoConvert.current, background,
      rows: files.map((path) => ({ id: path, name: baseName(path) })),
    });
  }, [dispatch]);

  // Files sent from Finder wait in Rust until this window takes them: on a
  // fresh launch they arrive before anything here is listening.
  const takeOpened = useCallback(async () => {
    const paths = await invoke<string[]>("take_opened");
    if (paths.length) void addPaths(paths, true);
  }, [addPaths]);

  // The status toast: what the background rows are doing, then gone.
  const noBackend = environment !== null && !environment.markitdown;
  const status = toastOf(queue);
  const toastText = status && noBackend ? "Set up tomd first" : status?.text;
  const toastTone = status && noBackend ? "error" : status?.tone;
  useEffect(() => {
    void invoke("set_toast", { toast: toastText ? { text: toastText, tone: toastTone } : null });
    if (!toastText || toastTone === "running") return;
    const timer = setTimeout(() => dispatch({ type: "seen" }), toastTone === "done" ? 2000 : 4000);
    return () => clearTimeout(timer);
  }, [toastText, toastTone, dispatch]);

  useEffect(() => {
    const stops = [
      getCurrentWebview().onDragDropEvent(({ payload }) => {
        setOver(payload.type === "enter" || payload.type === "over");
        if (payload.type === "drop") void addPaths(payload.paths);
      }),
      listen<string[]>(SOURCES_DROPPED, (e) => void addPaths(e.payload)),
      listen("sources-opened", () => void takeOpened()),
      listen(QUEUE_RUN, () => dispatch({ type: "enqueue" })),
      listen<string>("menu-action", (e) => {
        if (e.payload === "settings") setView("settings");
        if (e.payload === "youtube") { setView("list"); setYoutube(true); }
      }),
    ];
    void takeOpened();
    return () => stops.forEach((stop) => void stop.then((off) => off()));
  }, [addPaths, takeOpened, dispatch]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 2600);
    return () => clearTimeout(timer);
  }, [toast]);

  const taken = useMemo(
    () => queue.rows.flatMap((row) => (row.output ? [row.output] : [])), [queue.rows]);

  if (!settings) return null;
  const shell = "relative h-full bg-bg";
  if (!environment) {
    return <div className={`${shell} p-6 text-muted select-text`}>{error || "Starting…"}</div>;
  }
  if (!environment.markitdown) {
    return <div className={shell}><SetupPage environment={environment} onDone={refresh} /></div>;
  }
  if (view === "settings") {
    return (
      <div className={shell}>
        <SettingsPage settings={settings} environment={environment} onRefresh={refresh} onBack={() => setView("list")} />
      </div>
    );
  }

  const { rows, batch } = queue;
  const running = inFlight(queue) > 0;
  const selected = rows.filter((row) => row.selected);
  const runnable = rows.some((row) => row.state === "pending" || row.state === "error");
  const finished = batch.ok + batch.failed;
  const summary = running
    ? `Converting ${Math.min(finished + 1, batch.total)} of ${batch.total}`
    : batch.total
      ? `Done: ${batch.ok} converted${batch.failed ? `, ${batch.failed} failed` : ""}`
      : rows.length ? `${rows.length} file${rows.length > 1 ? "s" : ""}` : "";
  const broken = environment.health && !environment.health.ok;

  return (
    <div className={`${shell} flex flex-col ${over ? "outline-2 -outline-offset-2 outline-accent" : ""}`}>
      <header className="flex flex-wrap items-center gap-1.5 border-b border-line px-3 py-2.5">
        <Button onClick={async () => {
          const chosen = await open({ multiple: true });
          if (chosen) void addPaths(chosen);
        }}><Plus size={14} /> Add files</Button>
        <Button onClick={() => setYoutube(true)}><Video size={14} /> YouTube</Button>
        <span className="flex-1" />
        {selected.length > 0 ? (
          <>
            <Button title="Reveal selected" onClick={() =>
              selected.forEach((row) => void reveal(row.detail && row.state === "done" ? row.detail : row.id).catch(() => undefined))}>
              <FolderOpen size={14} />
            </Button>
            <Button title="Remove selected" onClick={() => dispatch({ type: "remove", ids: selected.map((r) => r.id) })}>
              <X size={14} /> Remove {selected.length}
            </Button>
          </>
        ) : (
          <Button disabled={running || !rows.length} title="Clear the list" onClick={() => dispatch({ type: "clear" })}>
            <Trash2 size={14} />
          </Button>
        )}
        {running
          ? <Button onClick={() => dispatch({ type: "stop" })}><Square size={13} /> Stop</Button>
          : <Button primary disabled={!runnable} onClick={() => dispatch({ type: "enqueue" })}><Play size={13} /> Run</Button>}
        <Button title="Settings" onClick={() => setView("settings")}><Cog size={14} /></Button>
      </header>

      {broken && (
        <button type="button" onClick={() => setView("settings")}
          className="bg-amber/15 px-3 py-1.5 text-left text-xs text-amber">
          MarkItDown needs a repair: some files will fail. Open Settings.
        </button>
      )}

      {rows.length ? (
        <ul className="flex-1 space-y-1.5 overflow-auto p-3">
          {rows.map((row) => (
            <FileRow key={row.id} row={row} onToast={setToast}
              onSelect={() => dispatch({ type: "select", id: row.id })} />
          ))}
        </ul>
      ) : (
        <div className="m-3 flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-line text-center">
          <p className="font-medium">Drop files or folders anywhere in this window</p>
          <p className="mt-1 text-xs text-muted">PDF, Word, Excel, PowerPoint, images, audio, HTML and more</p>
        </div>
      )}

      <footer className="border-t border-line px-3 py-2 text-xs text-muted">
        {running && (
          <div className="mb-1.5 h-1 overflow-hidden rounded bg-raised">
            <div className="h-full bg-accent transition-[width]"
              style={{ width: `${batch.total ? (finished / batch.total) * 100 : 0}%` }} />
          </div>
        )}
        {summary || " "}
      </footer>

      {toast && (
        <div role="status" className="absolute bottom-10 left-1/2 -translate-x-1/2 rounded-full bg-raised px-3.5 py-1.5 text-xs shadow-lg">
          {toast}
        </div>
      )}
      {youtube && (
        <YouTubeDialog folder={settings.youtube_folder} taken={taken} onClose={() => setYoutube(false)}
          onAdd={(row) => dispatch({ type: "add", rows: [row], enqueue: autoConvert.current })} />
      )}
    </div>
  );
}
