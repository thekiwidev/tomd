import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useEffect, useState } from "react";

export type Anchor =
  | "top-left" | "top-right" | "bottom-left"
  | "bottom-right" | "left-center" | "right-center";

/** What the drop zone does when a file drag starts. */
export type DragMode = "show" | "shake" | "small" | "option";

export type Settings = {
  dropzone_enabled: boolean;
  dock_anchor: Anchor;
  auto_convert_on_drop: boolean;
  menu_bar_only: boolean;
  youtube_folder: string;
  drag_mode: DragMode;
  finder_action: boolean;
};

export function setSetting<K extends keyof Settings>(key: K, value: Settings[K]) {
  return invoke<Settings>("set_setting", { key, value });
}

/** Live settings: changes from the tray or the other window arrive too. */
export function useSettings(): Settings | null {
  const [settings, setSettings] = useState<Settings | null>(null);
  useEffect(() => {
    invoke<Settings>("get_settings").then(setSettings);
    const stop = listen<Settings>("settings-changed", (e) => setSettings(e.payload));
    return () => void stop.then((off) => off());
  }, []);
  return settings;
}
