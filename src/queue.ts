// The conversion queue as plain data and a pure reducer. One file converts at
// a time; the runner that talks to the sidecar lives in `useQueue.ts`.

export type RowState = "pending" | "queued" | "running" | "done" | "error";

export type Row = {
  /** The source itself (a path or a URL): adding it twice is a no-op. */
  id: string;
  name: string;
  /** Explicit output path; only sources with no folder of their own (URLs). */
  output?: string;
  expectTranscript: boolean;
  state: RowState;
  /** The written .md path when done, the reason when failed. */
  detail?: string;
  selected: boolean;
  /** Sent from Finder: reported by the toast until it has been seen. */
  background: boolean;
};

export type NewRow = Pick<Row, "id" | "name"> & Partial<Pick<Row, "output" | "expectTranscript">>;

/** Progress of the run in flight, or the result of the last one. */
export type Batch = { total: number; ok: number; failed: number };

export type Queue = { rows: Row[]; batch: Batch };

export type Action =
  | { type: "add"; rows: NewRow[]; enqueue: boolean; background?: boolean }
  | { type: "seen" }
  | { type: "enqueue"; ids?: string[] }
  | { type: "start"; id: string }
  | { type: "finish"; id: string; ok: boolean; detail: string }
  | { type: "stop" }
  | { type: "clear" }
  | { type: "remove"; ids: string[] }
  | { type: "select"; id: string };

export const emptyQueue: Queue = { rows: [], batch: { total: 0, ok: 0, failed: 0 } };

const busy = (row: Row) => row.state === "queued" || row.state === "running";

export const inFlight = (queue: Queue) => queue.rows.filter(busy).length;

/** The row to convert next, or undefined while one is running or none wait. */
export function nextRow(queue: Queue): Row | undefined {
  if (queue.rows.some((row) => row.state === "running")) return undefined;
  return queue.rows.find((row) => row.state === "queued");
}

function enqueue(queue: Queue, wanted: (row: Row) => boolean): Queue {
  const eligible = (row: Row) =>
    wanted(row) && (row.state === "pending" || row.state === "error");
  const count = queue.rows.filter(eligible).length;
  if (!count) return queue;
  // A run that starts from idle begins a fresh tally; joining one extends it.
  const batch = inFlight(queue)
    ? { ...queue.batch, total: queue.batch.total + count }
    : { total: count, ok: 0, failed: 0 };
  const rows = queue.rows.map((row) =>
    eligible(row) ? { ...row, state: "queued" as const, detail: undefined } : row,
  );
  return { rows, batch };
}

export function reduce(queue: Queue, action: Action): Queue {
  switch (action.type) {
    case "add": {
      const background = action.background ?? false;
      const known = new Set(queue.rows.map((row) => row.id));
      const fresh = action.rows
        .filter((row, i, all) => !known.has(row.id) && all.findIndex((r) => r.id === row.id) === i)
        .map((row): Row => ({
          expectTranscript: false, ...row, state: "pending", selected: false, background,
        }));
      // A background add is a request to convert now, so a file already
      // listed runs again; anything else leaves listed files as they are.
      const again = new Set(background ? action.rows.map((row) => row.id) : []);
      const rows = queue.rows.map((row): Row =>
        again.has(row.id) && !busy(row) ? { ...row, state: "pending", background: true } : row,
      );
      const ids = new Set([...fresh.map((row) => row.id), ...again]);
      if (!fresh.length && !again.size) return queue;
      const added = { ...queue, rows: [...rows, ...fresh] };
      return action.enqueue || background ? enqueue(added, (row) => ids.has(row.id)) : added;
    }
    case "enqueue": {
      const ids = action.ids && new Set(action.ids);
      return enqueue(queue, (row) => !ids || ids.has(row.id));
    }
    case "start":
      return {
        ...queue,
        rows: queue.rows.map((row) =>
          row.id === action.id && row.state === "queued" ? { ...row, state: "running" } : row,
        ),
      };
    case "finish": {
      if (!queue.rows.some((row) => row.id === action.id && row.state === "running")) return queue;
      const key = action.ok ? "ok" : "failed";
      return {
        batch: { ...queue.batch, [key]: queue.batch[key] + 1 },
        rows: queue.rows.map((row) =>
          row.id === action.id
            ? { ...row, state: action.ok ? "done" : "error", detail: action.detail }
            : row,
        ),
      };
    }
    case "stop": {
      // The file being converted finishes; everything waiting goes back.
      const drained = queue.rows.filter((row) => row.state === "queued").length;
      if (!drained) return queue;
      return {
        batch: { ...queue.batch, total: queue.batch.total - drained },
        rows: queue.rows.map((row) =>
          row.state === "queued" ? { ...row, state: "pending" } : row,
        ),
      };
    }
    case "clear":
      return inFlight(queue) ? queue : emptyQueue;
    case "remove": {
      const ids = new Set(action.ids);
      return { ...queue, rows: queue.rows.filter((row) => !ids.has(row.id) || busy(row)) };
    }
    case "seen":
      return {
        ...queue,
        rows: queue.rows.map((row) => (row.background ? { ...row, background: false } : row)),
      };
    case "select":
      return {
        ...queue,
        rows: queue.rows.map((row) =>
          row.id === action.id ? { ...row, selected: !row.selected } : row,
        ),
      };
  }
}

export type Toast = { text: string; tone: "running" | "done" | "error" };

/** What the status toast says about the files sent from Finder, if anything. */
export function toastOf(queue: Queue): Toast | null {
  const rows = queue.rows.filter((row) => row.background);
  if (!rows.length) return null;
  const waiting = rows.filter(busy).length;
  if (waiting) {
    const text = rows.length === 1
      ? `Converting ${rows[0].name}`
      : `Converting ${rows.length - waiting + 1} of ${rows.length}`;
    return { text, tone: "running" };
  }
  const failed = rows.filter((row) => row.state === "error").length;
  if (!failed) return { text: rows.length === 1 ? "Done" : `${rows.length} converted`, tone: "done" };
  const text = rows.length === 1 ? "Failed" : `${rows.length - failed} converted, ${failed} failed`;
  return { text, tone: "error" };
}
