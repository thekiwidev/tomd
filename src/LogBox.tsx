import { useEffect, useRef } from "react";

/** Live output of an install or repair, pinned to its newest line. */
export function LogBox({ lines }: { lines: string[] }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => end.current?.scrollIntoView(), [lines]);
  if (!lines.length) return null;
  return (
    <pre className="max-h-48 overflow-auto rounded-md bg-bg p-2.5 font-mono text-[11px] leading-relaxed text-soft
      whitespace-pre-wrap select-text">
      {lines.join("\n")}
      <div ref={end} />
    </pre>
  );
}
