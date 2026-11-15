//! Persisted preferences. Rust owns them because several have effects outside
//! the webview (Dock icon, tray check mark, drag watcher).

use std::sync::atomic::Ordering;

use serde::Serialize;
use serde_json::{json, Value};
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_store::StoreExt;

use crate::{quick_action, windows, Shell};

const STORE: &str = "settings.json";
const BOOL_KEYS: [&str; 4] =
    ["dropzone_enabled", "auto_convert_on_drop", "menu_bar_only", "finder_action"];
/// How the drop zone behaves when a file drag starts (see `drag_watch`).
pub const DRAG_MODES: [&str; 4] = ["show", "shake", "small", "option"];

#[derive(Clone, Serialize)]
pub struct Settings {
    pub dropzone_enabled: bool,
    pub dock_anchor: String,
    pub auto_convert_on_drop: bool,
    pub menu_bar_only: bool,
    pub youtube_folder: String,
    pub drag_mode: String,
    pub finder_action: bool,
}

pub fn load(app: &AppHandle) -> Settings {
    let store = app.store(STORE).ok();
    let get = |key: &str| store.as_ref().and_then(|s| s.get(key));
    let flag = |key: &str, default: bool| get(key).and_then(|v| v.as_bool()).unwrap_or(default);
    let text = |key: &str| get(key).and_then(|v| v.as_str().map(str::to_owned));
    Settings {
        dropzone_enabled: flag("dropzone_enabled", true),
        dock_anchor: text("dock_anchor")
            .filter(|a| windows::ANCHORS.contains(&a.as_str()))
            .unwrap_or_else(|| windows::DEFAULT_ANCHOR.to_owned()),
        auto_convert_on_drop: flag("auto_convert_on_drop", false),
        menu_bar_only: flag("menu_bar_only", false),
        youtube_folder: text("youtube_folder").unwrap_or_default(),
        drag_mode: text("drag_mode")
            .filter(|m| DRAG_MODES.contains(&m.as_str()))
            .unwrap_or_else(|| DRAG_MODES[0].to_owned()),
        finder_action: flag("finder_action", true),
    }
}

/// Push the settings into everything outside the webview that reflects them.
pub fn apply(app: &AppHandle, settings: &Settings) {
    #[cfg(target_os = "macos")]
    {
        let policy = if settings.menu_bar_only {
            tauri::ActivationPolicy::Accessory
        } else {
            tauri::ActivationPolicy::Regular
        };
        let _ = app.set_activation_policy(policy);
    }
    let shell = app.state::<Shell>();
    let _ = shell.auto_convert_item.set_checked(settings.auto_convert_on_drop);
    shell.dropzone_enabled.store(settings.dropzone_enabled, Ordering::SeqCst);
    let mode = DRAG_MODES.iter().position(|m| *m == settings.drag_mode).unwrap_or(0);
    shell.drag_mode.store(mode as u8, Ordering::SeqCst);
    quick_action::sync(app, settings.finder_action);
    if !settings.dropzone_enabled {
        windows::close_dropzone(app);
    }
    windows::place_dropzone(app, &settings.dock_anchor);
}

fn validate(key: &str, value: &Value) -> Result<(), String> {
    let ok = match key {
        k if BOOL_KEYS.contains(&k) => value.is_boolean(),
        "dock_anchor" => value.as_str().is_some_and(|a| windows::ANCHORS.contains(&a)),
        "drag_mode" => value.as_str().is_some_and(|m| DRAG_MODES.contains(&m)),
        "youtube_folder" => value.is_string(),
        _ => return Err(format!("Unknown setting: {key}")),
    };
    ok.then_some(()).ok_or_else(|| format!("Invalid value for {key}"))
}

pub fn set(app: &AppHandle, key: &str, value: Value) -> Result<Settings, String> {
    validate(key, &value)?;
    let store = app.store(STORE).map_err(|e| e.to_string())?;
    store.set(key, value);
    store.save().map_err(|e| e.to_string())?;
    let settings = load(app);
    apply(app, &settings);
    let _ = app.emit("settings-changed", json!(settings));
    Ok(settings)
}

#[tauri::command]
pub fn get_settings(app: AppHandle) -> Settings {
    load(&app)
}

#[tauri::command]
pub fn set_setting(app: AppHandle, key: String, value: Value) -> Result<Settings, String> {
    set(&app, &key, value)
}

#[cfg(test)]
mod tests {
    use super::validate;
    use serde_json::json;

    #[test]
    fn rejects_unknown_keys_and_wrong_types() {
        assert!(validate("menu_bar_only", &json!(true)).is_ok());
        assert!(validate("menu_bar_only", &json!("yes")).is_err());
        assert!(validate("dock_anchor", &json!("top-left")).is_ok());
        assert!(validate("dock_anchor", &json!("middle")).is_err());
        assert!(validate("drag_mode", &json!("shake")).is_ok());
        assert!(validate("drag_mode", &json!("wiggle")).is_err());
        assert!(validate("finder_action", &json!(false)).is_ok());
        assert!(validate("anything_else", &json!(1)).is_err());
    }
}
