//! The two windows: the main window, and the floating drop zone that exists on
//! screen only while it is wanted (a file drag, or opened from the tray).

use std::sync::atomic::Ordering;

use serde_json::Value;
use tauri::{AppHandle, Emitter, LogicalSize, Manager, PhysicalPosition, WebviewWindow};

use crate::{settings, Shell};

pub const MAIN: &str = "main";
pub const DROPZONE: &str = "dropzone";
pub const TOAST: &str = "toast";
/// The drop zone at full size, and as the pill of the "small" drag mode.
const ZONE_SIZE: (f64, f64) = (300.0, 260.0);
const PILL_SIZE: (f64, f64) = (132.0, 40.0);
pub const DEFAULT_ANCHOR: &str = "bottom-right";
pub const ANCHORS: [&str; 6] = [
    "top-left", "top-right", "bottom-left", "bottom-right", "left-center", "right-center",
];
const MARGIN: f64 = 14.0;

pub fn show_main(app: &AppHandle) {
    if let Some(window) = app.get_webview_window(MAIN) {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
}

/// Top-left corner of a `size` window at `anchor` inside a work `area`
/// (x, y, width, height), inset by `margin` and clamped to stay inside.
fn anchor_position(anchor: &str, area: (i32, i32, i32, i32), size: (i32, i32), margin: i32) -> (i32, i32) {
    let (ax, ay, aw, ah) = area;
    let (w, h) = size;
    let (left, right) = (ax + margin, ax + aw - w - margin);
    let (top, bottom) = (ay + margin, ay + ah - h - margin);
    let mid_y = ay + (ah - h) / 2;
    let (x, y) = match anchor {
        "top-left" => (left, top),
        "top-right" => (right, top),
        "bottom-left" => (left, bottom),
        "left-center" => (left, mid_y),
        "right-center" => (right, mid_y),
        _ => (right, bottom),
    };
    (x.clamp(ax, (ax + aw - w).max(ax)), y.clamp(ay, (ay + ah - h).max(ay)))
}

pub fn place_dropzone(app: &AppHandle, anchor: &str) {
    place(app, DROPZONE, anchor);
    place(app, TOAST, anchor);
}

fn place(app: &AppHandle, label: &str, anchor: &str) {
    let Some(window) = app.get_webview_window(label) else { return };
    let (Ok(Some(monitor)), Ok(size)) = (window.primary_monitor(), window.outer_size()) else {
        return;
    };
    let area = monitor.work_area();
    let (x, y) = anchor_position(
        anchor,
        (area.position.x, area.position.y, area.size.width as i32, area.size.height as i32),
        (size.width as i32, size.height as i32),
        (MARGIN * monitor.scale_factor()) as i32,
    );
    let _ = window.set_position(PhysicalPosition::new(x, y));
}

/// Put the drop zone on screen without activating tomd: it appears mid-drag,
/// and stealing focus from the app being dragged from would be rude.
fn order_front(window: &WebviewWindow) {
    #[cfg(target_os = "macos")]
    {
        use objc2_app_kit::{NSWindow, NSWindowCollectionBehavior};
        let handle = window.clone();
        let _ = window.run_on_main_thread(move || {
            let Ok(ptr) = handle.ns_window() else { return };
            // SAFETY: Tauri hands out the window's live NSWindow, and this
            // closure runs on the main thread, where AppKit requires it.
            let ns_window = unsafe { &*(ptr as *const NSWindow) };
            ns_window.setCollectionBehavior(
                ns_window.collectionBehavior()
                    | NSWindowCollectionBehavior::CanJoinAllSpaces
                    | NSWindowCollectionBehavior::FullScreenAuxiliary,
            );
            ns_window.orderFrontRegardless();
        });
    }
    #[cfg(not(target_os = "macos"))]
    let _ = window.show();
}

pub fn show_dropzone(app: &AppHandle) {
    let Some(window) = app.get_webview_window(DROPZONE) else { return };
    // The two never share the anchor: the zone's rows already show progress.
    if let Some(toast) = app.get_webview_window(TOAST) {
        let _ = toast.hide();
    }
    place(app, DROPZONE, &settings::load(app).dock_anchor);
    order_front(&window);
}

/// Shrink the drop zone to a pill, or restore it; it stays at its anchor.
pub fn set_dropzone_compact(app: &AppHandle, compact: bool) {
    let Some(window) = app.get_webview_window(DROPZONE) else { return };
    let (width, height) = if compact { PILL_SIZE } else { ZONE_SIZE };
    let _ = window.set_size(LogicalSize::new(width, height));
    place(app, DROPZONE, &settings::load(app).dock_anchor);
}

/// The drop zone's rectangle in physical pixels: (x, y, width, height).
pub fn dropzone_rect(app: &AppHandle) -> Option<(f64, f64, f64, f64)> {
    let window = app.get_webview_window(DROPZONE)?;
    let (position, size) = (window.outer_position().ok()?, window.outer_size().ok()?);
    Some((position.x as f64, position.y as f64, size.width as f64, size.height as f64))
}

pub fn hide_dropzone_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window(DROPZONE) {
        let _ = window.hide();
    }
}

/// Show, change or (with null) put away the status toast. The text lives
/// here so the toast window can ask for it whenever it loads.
#[tauri::command]
pub fn set_toast(app: AppHandle, toast: Option<Value>) {
    let shell = app.state::<Shell>();
    *shell.toast.lock().unwrap_or_else(|e| e.into_inner()) = toast.clone();
    let _ = app.emit_to(TOAST, "toast-changed", &toast);
    let Some(window) = app.get_webview_window(TOAST) else { return };
    let zone_open = app
        .get_webview_window(DROPZONE)
        .is_some_and(|zone| zone.is_visible().unwrap_or(false));
    if toast.is_none() || zone_open {
        let _ = window.hide();
    } else {
        place(&app, TOAST, &settings::load(&app).dock_anchor);
        order_front(&window);
    }
}

#[tauri::command]
pub fn get_toast(app: AppHandle) -> Option<Value> {
    app.state::<Shell>().toast.lock().unwrap_or_else(|e| e.into_inner()).clone()
}

/// Opened on purpose: turns the feature on if it was off, and stays open.
pub fn open_dropzone(app: &AppHandle) {
    if !app.state::<Shell>().dropzone_enabled.load(Ordering::SeqCst) {
        if let Err(err) = settings::set(app, "dropzone_enabled", true.into()) {
            eprintln!("tomd: {err}");
        }
    }
    app.state::<Shell>().pinned.store(true, Ordering::SeqCst);
    set_dropzone_compact(app, false);
    show_dropzone(app);
}

pub fn close_dropzone(app: &AppHandle) {
    app.state::<Shell>().pinned.store(false, Ordering::SeqCst);
    if let Some(window) = app.get_webview_window(DROPZONE) {
        let _ = window.hide();
    }
}

#[tauri::command]
pub fn show_main_window(app: AppHandle) {
    show_main(&app);
}

#[tauri::command]
pub fn hide_dropzone(app: AppHandle) {
    close_dropzone(&app);
}

#[cfg(test)]
mod tests {
    use super::anchor_position;

    const AREA: (i32, i32, i32, i32) = (0, 25, 1000, 800);
    const SIZE: (i32, i32) = (300, 260);

    #[test]
    fn anchors_sit_inside_the_work_area_with_a_margin() {
        assert_eq!(anchor_position("top-left", AREA, SIZE, 14), (14, 39));
        assert_eq!(anchor_position("bottom-right", AREA, SIZE, 14), (686, 551));
        assert_eq!(anchor_position("right-center", AREA, SIZE, 14), (686, 295));
        assert_eq!(anchor_position("nonsense", AREA, SIZE, 14), (686, 551));
    }

    #[test]
    fn a_window_larger_than_the_area_is_clamped_to_its_origin() {
        assert_eq!(anchor_position("bottom-right", (10, 10, 100, 100), SIZE, 14), (10, 10));
    }
}
