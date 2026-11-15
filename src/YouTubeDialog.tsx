// A link has no folder of its own, so the dialog asks where the transcript
// goes (remembered) and what to call it.
import { open } from "@tauri-apps/plugin-dialog";
import { useEffect, useState } from "react";
import { call } from "./ipc";
import type { NewRow } from "./queue";
import { setSetting } from "./settings";
import { baseName, Button } from "./ui";

type Plan = { video_id: string | null; error: string | null; url?: string; output?: string };

type Props = { folder: string; taken: string[]; onAdd: (row: NewRow) => void; onClose: () => void };

export function YouTubeDialog({ folder, taken, onAdd, onClose }: Props) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);

  useEffect(() => {
    let stale = false;
    call<Plan>("youtube_plan", { url, title, folder, taken })
      .then((next) => !stale && setPlan(next), () => undefined);
    return () => { stale = true; };
  }, [url, title, folder, taken]);

  const chooseFolder = async () => {
    const chosen = await open({ directory: true, defaultPath: folder || undefined });
    if (typeof chosen === "string") await setSetting("youtube_folder", chosen);
  };

  const ready = plan?.url && plan.output;
  const input = "w-full rounded-md border border-line bg-bg px-2.5 py-1.5 outline-none focus:border-accent";
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/50 p-5" onClick={onClose}>
      <form className="w-full max-w-md space-y-3 rounded-xl border border-line bg-panel p-5"
        onClick={(e) => e.stopPropagation()}
        onSubmit={(e) => {
          e.preventDefault();
          if (!ready) return;
          onAdd({ id: plan.url!, name: baseName(plan.output!), output: plan.output, expectTranscript: true });
          onClose();
        }}>
        <div>
          <h2 className="text-base font-semibold">Add a YouTube video</h2>
          <p className="text-xs text-muted">tomd fetches the video's transcript and saves it as Markdown.</p>
        </div>
        <label className="block space-y-1">
          <span className="text-xs text-soft">Video link</span>
          <input autoFocus className={input} value={url} onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=…" />
          <span className={`block text-xs ${plan?.error ? "text-red" : "text-muted"}`}>
            {plan?.error ?? "A single video: youtube.com/watch?v=… or youtu.be/…. Not Shorts, playlists or channels."}
          </span>
        </label>
        <label className="block space-y-1">
          <span className="text-xs text-soft">Title (used for the file name)</span>
          <input className={input} value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <div className="space-y-1">
          <span className="text-xs text-soft">Save to</span>
          <div className="flex items-center gap-2">
            <span className="min-w-0 flex-1 truncate text-xs text-muted" title={folder}>{folder || "No folder chosen"}</span>
            <Button onClick={chooseFolder}>Choose…</Button>
          </div>
        </div>
        <p className="truncate text-xs text-soft" title={plan?.output}>
          {plan?.output ? `Will save ${baseName(plan.output)}` : " "}
        </p>
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button primary type="submit" disabled={!ready}>Add</Button>
        </div>
      </form>
    </div>
  );
}
