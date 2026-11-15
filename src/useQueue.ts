// The queue's runner: the main window owns the queue, converts one row at a
// time through the sidecar, and mirrors the state to the drop zone window.
import { emit } from "@tauri-apps/api/event";
import { useEffect, useReducer } from "react";
import { call } from "./ipc";
import { emptyQueue, nextRow, reduce } from "./queue";

export const QUEUE_CHANGED = "queue-changed";

export function useQueue(markitdown: string | null) {
  const [queue, dispatch] = useReducer(reduce, emptyQueue);

  useEffect(() => {
    const row = markitdown ? nextRow(queue) : undefined;
    if (!row) return;
    dispatch({ type: "start", id: row.id });
    call<{ detail: string }>("convert_file", {
      markitdown_exe: markitdown,
      source: row.id,
      output: row.output,
      expect_transcript: row.expectTranscript,
    }).then(
      (data) => dispatch({ type: "finish", id: row.id, ok: true, detail: data.detail }),
      (error: Error) => dispatch({ type: "finish", id: row.id, ok: false, detail: error.message }),
    );
  }, [queue, markitdown]);

  useEffect(() => void emit(QUEUE_CHANGED, queue), [queue]);

  return [queue, dispatch] as const;
}
