// What the device has: Python, uv, MarkItDown and whether it can do the job.
import { useCallback, useEffect, useState } from "react";
import { call } from "./ipc";

export type Health = {
  version_str: string | null;
  version_ok: boolean;
  missing_features: string[] | null;
  ok: boolean;
};

export type Environment = {
  markitdown: string | null;
  health: Health | null;
  python: string | null;
  python_version: string | null;
  uv: string | null;
};

export type Foreign = { interpreter: string; version: string; healthy: boolean };

/** A shallow report at once (so the window is usable), then the health probe. */
export function useEnvironment() {
  const [environment, setEnvironment] = useState<Environment | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      await call("invalidate_health_cache");
      setEnvironment(await call<Environment>("environment_report", { deep: false }));
      setEnvironment(await call<Environment>("environment_report", { deep: true }));
      setError("");
    } catch (failure) {
      setError(String(failure));
    }
  }, []);

  useEffect(() => void refresh(), [refresh]);
  return { environment, error, refresh };
}
