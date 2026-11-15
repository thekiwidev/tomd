//! The menu bar icon. A native status item and menu: nothing here goes through
//! a UI toolkit's event handling.

use tauri::image::Image;
use tauri::menu::{CheckMenuItem, Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::{AppHandle, Emitter, Wry};

use crate::{settings, windows};

/// Builds the tray and returns the auto-convert item so settings can keep its
/// check mark in sync.
pub fn build(app: &AppHandle, auto_convert: bool) -> tauri::Result<CheckMenuItem<Wry>> {
    let item = |id: &str, text: &str| MenuItem::with_id(app, id, text, true, None::<&str>);
    let auto = CheckMenuItem::with_id(
        app, "auto", "Auto-convert on drop", true, auto_convert, None::<&str>,
    )?;
    let menu = Menu::with_items(
        app,
        &[
            &item("window", "Open window view")?,
            &item("dropzone", "Open drop zone")?,
            &item("youtube", "Add YouTube video…")?,
            &PredefinedMenuItem::separator(app)?,
            &item("settings", "Settings…")?,
            &auto,
            &PredefinedMenuItem::separator(app)?,
            &item("quit", "Quit tomd")?,
        ],
    )?;

    let auto_item = auto.clone();
    TrayIconBuilder::with_id("tomd")
        .icon(Image::from_bytes(include_bytes!("../icons/tray.png"))?)
        .icon_as_template(true)
        .tooltip("tomd")
        .menu(&menu)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "window" => windows::show_main(app),
            "dropzone" => windows::open_dropzone(app),
            // These two live in the main window, so it has to be visible.
            id @ ("youtube" | "settings") => {
                windows::show_main(app);
                let _ = app.emit("menu-action", id);
            }
            "auto" => {
                let checked = auto_item.is_checked().unwrap_or(false);
                if let Err(err) = settings::set(app, "auto_convert_on_drop", checked.into()) {
                    eprintln!("tomd: {err}");
                }
            }
            "quit" => app.exit(0),
            _ => {}
        })
        .build(app)?;
    Ok(auto)
}
