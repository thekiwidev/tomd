// The floating drop zone. It owns no queue: drops are handed to the main
// window, which converts them and mirrors the queue back here.
import { invoke } from "@tauri-apps/api/core";
import { emitTo, listen } from "@tauri-apps/api/event";
import { getCurrentWebview } from "@tauri-apps/api/webview";
import { AppWindow, Play, X } from "lucide-react";
import { useEffect, useState } from "react";
import { FileRow } from "./FileRow";
import { QUEUE_RUN, SOURCES_DROPPED } from "./MainWindow";
import { emptyQueue, inFlight, type Queue } from "./queue";
import { QUEUE_CHANGED } from "./useQueue";

export function DropZone() {
  const [queue, setQueue] = useState<Queue>(emptyQueue);
  const [over, setOver] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    const stops = [
      getCurrentWebview().onDragDropEvent(({ payload }) => {
        setOver(payload.type === "enter" || payload.type === "over");
        if (payload.type === "drop") void emitTo("main", SOURCES_DROPPED, payload.paths);
      }),
      listen<Queue>(QUEUE_CHANGED, (e) => setQueue(e.payload)),
    ];
    return () => stops.forEach((stop) => void stop.then((off) => off()));
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 2000);
    return () => clearTimeout(timer);
  }, [toast]);

  const runnable = !inFlight(queue) && queue.rows.some((row) => row.state === "pending" || row.state === "error");
  const chip = "rounded p-1 text-soft hover:bg-raised-hover hover:text-text";
  return (
    <main className={`flex h-full flex-col rounded-[14px] border bg-panel/95 ${over ? "border-accent bg-raised" : "border-line"}
      [@media(max-height:80px)]:[&>:not(.pill)]:hidden`}>
      {/* The "start small" drag mode shrinks the window; only this shows then. */}
      <p className="pill hidden flex-1 items-center justify-center text-xs text-soft [@media(max-height:80px)]:flex">
        Drop to convert
      </p>
      <header className="flex items-center gap-1 px-3 pt-2.5">
        <strong className="flex-1 text-xs">{toast || "tomd"}</strong>
        {runnable && (
          <button type="button" title="Run" className={chip} onClick={() => emitTo("main", QUEUE_RUN)}>
            <Play size={13} />
          </button>
        )}
        <button type="button" title="Open window view" className={chip} onClick={() => invoke("show_main_window")}>
          <AppWindow size={13} />
        </button>
        <button type="button" title="Close" className={chip} onClick={() => invoke("hide_dropzone")}>
          <X size={13} />
        </button>
      </header>
      {queue.rows.length ? (
        <ul className="flex-1 space-y-1 overflow-auto p-2 [&>li]:bg-bg/60 [&>li]:px-2 [&>li]:py-1.5">
          {queue.rows.map((row) => <FileRow key={row.id} row={row} compact onToast={setToast} />)}
        </ul>
      ) : (
        <p className="flex flex-1 items-center justify-center text-xs text-muted">Drop files here to convert</p>
      )}
    </main>
  );
}
