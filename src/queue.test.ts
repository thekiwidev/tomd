import { describe, expect, it } from "vitest";
import { type Action, emptyQueue, inFlight, nextRow, type Queue, reduce, toastOf } from "./queue";

const run = (actions: Action[], from: Queue = emptyQueue) => actions.reduce(reduce, from);
const add = (ids: string[], enqueue = false): Action => ({
  type: "add", enqueue, rows: ids.map((id) => ({ id, name: id })),
});
const states = (queue: Queue) => queue.rows.map((row) => row.state);

describe("queue", () => {
  it("adds each source once and leaves it pending", () => {
    const queue = run([add(["a", "b", "a"]), add(["b", "c"])]);
    expect(queue.rows.map((row) => row.id)).toEqual(["a", "b", "c"]);
    expect(states(queue)).toEqual(["pending", "pending", "pending"]);
  });

  it("auto-convert queues only the rows just added", () => {
    const queue = run([add(["a"]), add(["b"], true)]);
    expect(states(queue)).toEqual(["pending", "queued"]);
    expect(queue.batch.total).toBe(1);
  });

  it("converts one file at a time, in order", () => {
    let queue = run([add(["a", "b"], true)]);
    expect(nextRow(queue)?.id).toBe("a");
    queue = reduce(queue, { type: "start", id: "a" });
    expect(nextRow(queue)).toBeUndefined();
    queue = reduce(queue, { type: "finish", id: "a", ok: true, detail: "/a.md" });
    expect(nextRow(queue)?.id).toBe("b");
    expect(queue.rows[0]).toMatchObject({ state: "done", detail: "/a.md" });
  });

  it("stop returns waiting rows to pending and lets the running one finish", () => {
    let queue = run([add(["a", "b", "c"], true), { type: "start", id: "a" }, { type: "stop" }]);
    expect(states(queue)).toEqual(["running", "pending", "pending"]);
    expect(queue.batch.total).toBe(1);
    queue = reduce(queue, { type: "finish", id: "a", ok: false, detail: "boom" });
    expect(queue.rows[0]).toMatchObject({ state: "error", detail: "boom" });
    expect(queue.batch).toEqual({ total: 1, ok: 0, failed: 1 });
    expect(inFlight(queue)).toBe(0);
  });

  it("run retries failed rows and starts a fresh tally", () => {
    const queue = run([
      add(["a"], true), { type: "start", id: "a" },
      { type: "finish", id: "a", ok: false, detail: "boom" }, { type: "enqueue" },
    ]);
    expect(queue.rows[0]).toMatchObject({ state: "queued", detail: undefined });
    expect(queue.batch).toEqual({ total: 1, ok: 0, failed: 0 });
  });

  it("never clears or removes a row that is in flight", () => {
    const busy = run([add(["a", "b"], true), { type: "start", id: "a" }]);
    expect(reduce(busy, { type: "clear" })).toBe(busy);
    expect(reduce(busy, { type: "remove", ids: ["a", "b"] }).rows).toHaveLength(2);
    const idle = run([add(["a", "b"])]);
    expect(reduce(idle, { type: "remove", ids: ["a"] }).rows.map((r) => r.id)).toEqual(["b"]);
    expect(reduce(idle, { type: "clear" })).toBe(emptyQueue);
  });

  it("a background add converts at once and re-runs a finished row", () => {
    const finished = run([
      add(["a"], true), { type: "start", id: "a" },
      { type: "finish", id: "a", ok: true, detail: "/a.md" },
    ]);
    const queue = reduce(finished, {
      type: "add", enqueue: false, background: true,
      rows: [{ id: "a", name: "a" }, { id: "b", name: "b" }],
    });
    expect(states(queue)).toEqual(["queued", "queued"]);
    expect(queue.rows.every((row) => row.background)).toBe(true);
    expect(queue.batch).toEqual({ total: 2, ok: 0, failed: 0 });
  });

  it("a background add leaves a row that is converting alone", () => {
    const busy = run([add(["a"], true), { type: "start", id: "a" }]);
    const queue = reduce(busy, {
      type: "add", enqueue: false, background: true, rows: [{ id: "a", name: "a" }],
    });
    expect(queue.rows).toEqual(busy.rows);
  });

  it("the toast follows background rows only, until it is seen", () => {
    const bg = (ids: string[]): Action => ({
      type: "add", enqueue: false, background: true, rows: ids.map((id) => ({ id, name: id })),
    });
    expect(toastOf(run([add(["x"], true)]))).toBeNull();

    let queue = run([bg(["a"])]);
    expect(toastOf(queue)).toEqual({ text: "Converting a", tone: "running" });
    queue = run([{ type: "start", id: "a" }, { type: "finish", id: "a", ok: true, detail: "/a.md" }], queue);
    expect(toastOf(queue)).toEqual({ text: "Done", tone: "done" });

    queue = run([bg(["b", "c"]), { type: "start", id: "b" }], queue);
    expect(toastOf(queue)).toEqual({ text: "Converting 2 of 3", tone: "running" });
    queue = run([
      { type: "finish", id: "b", ok: false, detail: "boom" },
      { type: "start", id: "c" }, { type: "finish", id: "c", ok: true, detail: "/c.md" },
    ], queue);
    expect(toastOf(queue)).toEqual({ text: "2 converted, 1 failed", tone: "error" });

    queue = reduce(queue, { type: "seen" });
    expect(toastOf(queue)).toBeNull();
    expect(queue.rows.find((row) => row.id === "b")?.state).toBe("error");
  });

  it("ignores a finish for a row that is not running", () => {
    const queue = run([add(["a"])]);
    expect(reduce(queue, { type: "finish", id: "a", ok: true, detail: "x" })).toBe(queue);
  });
});
