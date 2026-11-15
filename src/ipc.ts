// The Python sidecar, as promises. Rust only moves lines (`sidecar.rs`);
// replies are matched to requests here, by id.
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow } from "@tauri-apps/api/window";

type Reply =
  | { id: string; event: "log"; line: string }
  | { id: string; event: "result"; ok: true; data: unknown }
  | { id: string; event: "result"; ok: false; error: string };

type Pending = {
  resolve: (data: unknown) => void;
  reject: (error: Error) => void;
  onLog?: (line: string) => void;
};

const pending = new Map<string, Pending>();
// Every window hears every reply, so ids carry the window's label.
const prefix = getCurrentWindow().label;
let counter = 0;

const ready = listen<string>("sidecar-message", ({ payload }) => {
  let reply: Reply;
  try {
    reply = JSON.parse(payload);
  } catch {
    return; // not protocol output
  }
  const request = pending.get(reply.id);
  if (!request) return;
  if (reply.event === "log") {
    request.onLog?.(reply.line);
    return;
  }
  pending.delete(reply.id);
  if (reply.ok) request.resolve(reply.data);
  else request.reject(new Error(reply.error));
});

export async function call<T>(
  method: string,
  params: Record<string, unknown> = {},
  onLog?: (line: string) => void,
): Promise<T> {
  await ready;
  const id = `${prefix}:${++counter}`;
  const result = new Promise<T>((resolve, reject) => {
    pending.set(id, { resolve: resolve as (data: unknown) => void, reject, onLog });
  });
  try {
    await invoke("sidecar_send", { line: JSON.stringify({ id, method, params }) });
  } catch (error) {
    pending.delete(id);
    throw new Error(String(error));
  }
  return result;
}
