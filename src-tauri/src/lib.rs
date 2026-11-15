//! tomd's desktop shell: windows, tray, settings, the drag watcher and the
//! Python sidecar. The UI lives in the webview (`src/`); conversion lives in
//! the sidecar (`sidecar.py`).

#[cfg(target_os = "macos")]
mod drag_watch;
mod quick_action;
mod settings;
mod shake;
mod sidecar;
mod tray;
mod windows;

use std::sync::atomic::{AtomicBool, AtomicU8, Ordering};
use std::sync::Mutex;

use tauri::menu::CheckMenuItem;
use tauri::{DragDropEvent, Emitter, Manager, RunEvent, WindowEvent, Wry};
use tauri_plugin_autostart::{MacosLauncher, ManagerExt};
use tauri_plugin_window_state::StateFlags;

/// Live shell state shared by the tray, the drag watcher and the commands.
pub struct Shell {
    pub auto_convert_item: CheckMenuItem<Wry>,
    pub dropzone_enabled: AtomicBool,
    /// The drop zone was opened on purpose (tray, or a file landed on it) and
    /// stays until the user closes it.
    pub pinned: AtomicBool,
    /// A file drag is in progress and the drop zone was summoned for it.
    pub drag_active: AtomicBool,
    /// Index into `settings::DRAG_MODES`.
    pub drag_mode: AtomicU8,
    /// What the status toast shows; None while it is put away.
    pub toast: Mutex<Option<serde_json::Value>>,
}

/// Files opened with tomd (the Finder Quick Action, or a drop on the Dock
/// icon) that the main window has not taken yet. Its own state, managed
/// before the app is built: on a fresh launch macOS delivers the files before
/// `setup` has run, when `Shell` does not exist yet (a panic there aborts the
/// app from inside the Apple Event handler; LOG L-014).
#[derive(Default)]
struct Opened(Mutex<Vec<String>>);

#[tauri::command]
fn take_opened(app: tauri::AppHandle) -> Vec<String> {
    std::mem::take(&mut *app.state::<Opened>().0.lock().unwrap_or_else(|e| e.into_inner()))
}

/// tomd 0.1.x registered its own LaunchAgent. Left in place it would start a
/// second copy at login, so hand the preference over to the autostart plugin.
fn migrate_login_item(app: &tauri::AppHandle) {
    // Never from a debug build: it would register target/debug as the login item.
    if cfg!(debug_assertions) {
        return;
    }
    let Ok(home) = app.path().home_dir() else { return };
    let old = home.join("Library/LaunchAgents/me.thekiwidev.tomd.plist");
    if old.exists() && std::fs::remove_file(&old).is_ok() {
        let _ = app.autolaunch().enable();
    }
}

/// Put a converted file's Markdown on the clipboard. Reads only `.md` files:
/// the webview has no general file access and this must not become one.
#[tauri::command]
fn copy_markdown(app: tauri::AppHandle, path: String) -> Result<(), String> {
    use tauri_plugin_clipboard_manager::ClipboardExt;
    if !path.to_lowercase().ends_with(".md") {
        return Err("Only Markdown files can be copied".into());
    }
    let text = std::fs::read_to_string(&path).map_err(|e| e.to_string())?;
    app.clipboard().write_text(text).map_err(|e| e.to_string())
}

/// tomd restores nothing at launch. Without this, macOS answers a crash with
/// a "reopen windows?" dialog on the next start, which blocks a background
/// launch from Finder until someone clicks it.
#[cfg(target_os = "macos")]
fn ignore_saved_window_state() {
    use objc2_foundation::{NSString, NSUserDefaults};
    NSUserDefaults::standardUserDefaults()
        .setBool_forKey(true, &NSString::from_str("ApplePersistenceIgnoreState"));
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    #[cfg(target_os = "macos")]
    ignore_saved_window_state();
    let app = tauri::Builder::default()
        .manage(Opened::default())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(
            tauri_plugin_window_state::Builder::new()
                .with_denylist(&[windows::DROPZONE, windows::TOAST])
                // Visibility is tomd's call (menu-bar-only mode), not a saved state.
                .with_state_flags(StateFlags::all() & !StateFlags::VISIBLE)
                .build(),
        )
        .plugin(tauri_plugin_autostart::init(MacosLauncher::LaunchAgent, None))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_drag::init())
        .invoke_handler(tauri::generate_handler![
            settings::get_settings,
            settings::set_setting,
            sidecar::sidecar_send,
            windows::hide_dropzone,
            windows::show_main_window,
            windows::set_toast,
            windows::get_toast,
            quick_action::quick_action_available,
            take_opened,
            copy_markdown,
        ])
        .setup(|app| {
            let handle = app.handle().clone();
            let current = settings::load(&handle);

            app.manage(sidecar::Sidecar::spawn(&handle));
            let auto_convert_item = tray::build(&handle, current.auto_convert_on_drop)?;
            app.manage(Shell {
                auto_convert_item,
                dropzone_enabled: AtomicBool::new(current.dropzone_enabled),
                pinned: AtomicBool::new(false),
                drag_active: AtomicBool::new(false),
                drag_mode: AtomicU8::new(0),
                toast: Mutex::new(None),
            });

            settings::apply(&handle, &current);
            migrate_login_item(&handle);
            // The Finder Quick Action starts tomd with --background: convert, no window.
            let background = std::env::args().any(|arg| arg == "--background");
            if !current.menu_bar_only && !background {
                windows::show_main(&handle);
            }

            #[cfg(target_os = "macos")]
            drag_watch::install(handle.clone());
            Ok(())
        })
        .on_window_event(|window, event| match (window.label(), event) {
            // tomd outlives its window: closing it leaves the menu bar icon.
            (windows::MAIN, WindowEvent::CloseRequested { api, .. }) => {
                api.prevent_close();
                let _ = window.hide();
            }
            // A file landed on the drop zone: keep it open to show the result.
            (windows::DROPZONE, WindowEvent::DragDrop(DragDropEvent::Drop { .. })) => {
                window.state::<Shell>().pinned.store(true, Ordering::SeqCst);
            }
            _ => {}
        })
        .build(tauri::generate_context!())
        .expect("error while building tomd");

    app.run(|handle, event| match event {
        #[cfg(target_os = "macos")]
        RunEvent::Reopen { .. } => windows::show_main(handle),
        #[cfg(target_os = "macos")]
        RunEvent::Opened { urls } => {
            let paths = urls
                .iter()
                .filter_map(|url| url.to_file_path().ok())
                .map(|path| path.to_string_lossy().into_owned());
            handle.state::<Opened>().0.lock().unwrap_or_else(|e| e.into_inner()).extend(paths);
            let _ = handle.emit_to(windows::MAIN, "sources-opened", ());
        }
        RunEvent::Exit => handle.state::<sidecar::Sidecar>().kill(),
        _ => {}
    });
}
