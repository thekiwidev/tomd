//! The Finder Quick Action "Convert to Markdown": a generated Automator
//! service bundle in ~/Library/Services whose one shell line hands the chosen
//! files to tomd. An unsigned app cannot add a top-level Finder menu item;
//! this is what macOS allows without a signed Finder extension.

use std::path::{Path, PathBuf};

use tauri::{AppHandle, Manager};

const BUNDLE: &str = "Library/Services/Convert to Markdown.workflow";
const INFO: &str = include_str!("../quick-action/Info.plist");
const DOCUMENT: &str = include_str!("../quick-action/document.wflow");
const COMMAND_SLOT: &str = "__TOMD_COMMAND__";

/// The .app this process runs from, if it is an installed one. A build
/// folder is refused: the entry would break on the next clean.
fn installed_app(exe: &Path) -> Option<PathBuf> {
    let app = exe.ancestors().nth(3)?;
    let is_app = app.extension().is_some_and(|ext| ext == "app");
    (is_app && !app.components().any(|part| part.as_os_str() == "target")).then(|| app.to_owned())
}

fn xml_escape(text: &str) -> String {
    text.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;")
}

/// `-g` keeps tomd in the background; `--background` is only seen by a fresh
/// launch and stops it from opening its window.
fn command(app: &Path) -> String {
    format!("open -g -a \"{}\" \"$@\" --args --background", app.display())
}

fn document(app: &Path) -> String {
    DOCUMENT.replace(COMMAND_SLOT, &xml_escape(&command(app)))
}

fn bundle_dir(app: &AppHandle) -> Option<PathBuf> {
    app.path().home_dir().ok().map(|home| home.join(BUNDLE))
}

fn refresh_services() {
    let _ = std::process::Command::new("/System/Library/CoreServices/pbs").arg("-update").spawn();
}

/// Whether this copy of tomd may own the Finder entry.
pub fn available() -> bool {
    std::env::current_exe().ok().and_then(|exe| installed_app(&exe)).is_some()
}

/// Make the bundle on disk match the setting. Does nothing from a build
/// folder, so a development run never touches an installed app's entry.
pub fn sync(app: &AppHandle, enabled: bool) {
    let Some(target) = std::env::current_exe().ok().and_then(|exe| installed_app(&exe)) else {
        return;
    };
    let Some(dir) = bundle_dir(app) else { return };
    let contents = dir.join("Contents");
    let wanted = document(&target);
    let current = std::fs::read_to_string(contents.join("document.wflow")).ok();
    let result = match (enabled, current) {
        (true, Some(found)) if found == wanted => return,
        (true, _) => std::fs::create_dir_all(&contents)
            .and_then(|()| std::fs::write(contents.join("Info.plist"), INFO))
            .and_then(|()| std::fs::write(contents.join("document.wflow"), wanted)),
        (false, Some(_)) => std::fs::remove_dir_all(&dir),
        (false, None) => return,
    };
    match result {
        Ok(()) => refresh_services(),
        Err(err) => eprintln!("tomd: Finder Quick Action: {err}"),
    }
}

#[tauri::command]
pub fn quick_action_available() -> bool {
    available()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn only_an_installed_app_owns_the_entry() {
        let installed = Path::new("/Applications/tomd.app/Contents/MacOS/tomd");
        assert_eq!(installed_app(installed), Some(PathBuf::from("/Applications/tomd.app")));
        let build = Path::new("/src/tomd/src-tauri/target/debug/bundle/macos/tomd.app/Contents/MacOS/tomd");
        assert_eq!(installed_app(build), None);
        assert_eq!(installed_app(Path::new("/src/tomd/src-tauri/target/debug/tomd")), None);
    }

    #[test]
    fn the_document_carries_the_escaped_command() {
        let text = document(Path::new("/Applications/A & B/tomd.app"));
        assert!(!text.contains(COMMAND_SLOT));
        assert!(text.contains("open -g -a \"/Applications/A &amp; B/tomd.app\" \"$@\" --args --background"));
        assert!(INFO.contains("runWorkflowAsService") && INFO.contains("com.adobe.pdf"));
    }
}
