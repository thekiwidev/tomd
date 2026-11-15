// The status toast for files sent from Finder: one line at the drop zone's
// anchor. Rust holds what it says (`set_toast`); this window only draws it.
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { Check, CircleAlert, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";
import type { Toast as ToastState } from "./queue";

const ICONS = {
  running: <LoaderCircle size={15} className="shrink-0 animate-spin text-accent" />,
  done: <Check size={15} className="shrink-0 text-green" />,
  error: <CircleAlert size={15} className="shrink-0 text-red" />,
};

export function Toast() {
  const [toast, setToast] = useState<ToastState | null>(null);

  useEffect(() => {
    void invoke<ToastState | null>("get_toast").then(setToast);
    const stop = listen<ToastState | null>("toast-changed", (e) => setToast(e.payload));
    return () => void stop.then((off) => off());
  }, []);

  if (!toast) return null;
  return (
    <button type="button" title="Open tomd"
      className="flex h-full w-full items-center gap-2.5 rounded-full border border-line bg-panel/95 px-4 text-left"
      onClick={() => { void invoke("show_main_window"); void invoke("set_toast", { toast: null }); }}>
      {ICONS[toast.tone]}
      <span className="truncate">{toast.text}</span>
    </button>
  );
}
