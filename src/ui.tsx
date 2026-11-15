// Small shared pieces: the button, the switch and file actions.
import { startDrag } from "@crabnebula/tauri-plugin-drag";
import { invoke } from "@tauri-apps/api/core";
import { revealItemInDir } from "@tauri-apps/plugin-opener";
import type { ButtonHTMLAttributes, DragEvent } from "react";
import { DRAG_ICON } from "./dragIcon";

export const baseName = (path: string) => path.split(/[\\/]/).pop() || path;

export const copyMarkdown = (path: string) => invoke<void>("copy_markdown", { path });
export const reveal = (path: string) => revealItemInDir(path);

/** Spread on an element to let the user drag `path` out to another app. */
export const dragOut = (path: string) => ({
  draggable: true,
  onDragStart: (event: DragEvent) => {
    event.preventDefault();
    void startDrag({ item: [path], icon: DRAG_ICON });
  },
});

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { primary?: boolean };

export function Button({ primary, className = "", ...props }: ButtonProps) {
  const tone = primary
    ? "bg-accent-strong text-white hover:bg-accent"
    : "bg-raised text-text hover:bg-raised-hover";
  return (
    <button type="button" {...props}
      className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium
        disabled:opacity-40 disabled:pointer-events-none ${tone} ${className}`} />
  );
}

export function Switch(props: { label: string; hint?: string; checked: boolean; onChange: (on: boolean) => void }) {
  return (
    <label className="flex items-center justify-between gap-4 py-2">
      <span>
        <span className="block">{props.label}</span>
        {props.hint && <span className="block text-xs text-muted">{props.hint}</span>}
      </span>
      <input type="checkbox" role="switch" className="h-4 w-4 accent-accent"
        checked={props.checked} onChange={(e) => props.onChange(e.target.checked)} />
    </label>
  );
}
