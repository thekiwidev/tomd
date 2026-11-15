import { Check, CircleAlert, Clock, Copy, FileText, FolderOpen, GripVertical, LoaderCircle } from "lucide-react";
import type { Row } from "./queue";
import { baseName, copyMarkdown, dragOut, reveal } from "./ui";

const STATUS = {
  pending: { icon: FileText, tone: "text-muted", text: "Ready to convert" },
  queued: { icon: Clock, tone: "text-muted", text: "Waiting" },
  running: { icon: LoaderCircle, tone: "text-accent", text: "Converting…" },
  done: { icon: Check, tone: "text-green", text: "" },
  error: { icon: CircleAlert, tone: "text-red", text: "" },
} as const;

type Props = {
  row: Row;
  compact?: boolean;
  onSelect?: () => void;
  onToast: (text: string) => void;
};

export function FileRow({ row, compact, onSelect, onToast }: Props) {
  const status = STATUS[row.state];
  const Icon = status.icon;
  const done = row.state === "done" && row.detail;
  const sub = row.state === "done" ? baseName(row.detail ?? "") : row.detail || status.text;
  const chip = "rounded p-1 text-soft hover:bg-raised-hover hover:text-text";

  return (
    <li className="flex items-center gap-2.5 rounded-lg bg-panel px-3 py-2">
      {onSelect && (
        <input type="checkbox" aria-label={`Select ${row.name}`} className="h-3.5 w-3.5 shrink-0 accent-accent"
          checked={row.selected} onChange={onSelect} />
      )}
      <Icon size={15} className={`shrink-0 ${status.tone} ${row.state === "running" ? "animate-spin" : ""}`} />
      <div className="min-w-0 flex-1">
        <div className="truncate" title={row.id}>{row.name}</div>
        {!compact && (
          <div className={`truncate text-xs ${row.state === "error" ? "text-red" : "text-muted"}`} title={sub}>
            {sub}
          </div>
        )}
      </div>
      {done && (
        <div className="flex shrink-0 items-center gap-0.5">
          <button type="button" title="Copy Markdown" className={chip}
            onClick={() => copyMarkdown(done).then(() => onToast("Markdown copied"), (e) => onToast(String(e)))}>
            <Copy size={14} />
          </button>
          <span title="Drag the .md file out" className={`${chip} cursor-grab`} {...dragOut(done)}>
            <GripVertical size={14} />
          </span>
          <button type="button" title="Reveal in Finder" className={chip}
            onClick={() => reveal(done).catch((e) => onToast(String(e)))}>
            <FolderOpen size={14} />
          </button>
        </div>
      )}
    </li>
  );
}
