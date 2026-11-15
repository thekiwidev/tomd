//! Summons the drop zone when a file drag starts anywhere on screen.
//!
//! tomd 0.1.x kept an invisible always-on-top window at the anchor to catch an
//! approaching drag; that window swallowed every click in its corner. Here
//! nothing is on screen while idle. A file drag is recognised by two cheap
//! facts: the left mouse button is down, and the system drag pasteboard has
//! changed and carries files. Both are polled, because a global NSEvent
//! monitor did not report drags on macOS 27 (docs/ai/LOG.md L-005).
//!
//! The zone can cover the place a file was meant to go, so the "drag mode"
//! setting chooses how it gets out of the way: shake the pointer, hold
//! Option, or start as a small pill that grows when the file comes near.

use std::sync::atomic::Ordering;
use std::time::{Duration, Instant};

use objc2_app_kit::{
    NSEvent, NSEventModifierFlags, NSPasteboard, NSPasteboardNameDrag, NSPasteboardTypeFileURL,
};
use objc2_foundation::{NSArray, NSString};
use tauri::{AppHandle, Manager};

use crate::shake::Shake;
use crate::{settings, windows, Shell};

const POLL: Duration = Duration::from_millis(120);
/// While a drag is on, fast enough to see a shake and to grow the pill promptly.
const DRAG_POLL: Duration = Duration::from_millis(30);
/// The pill grows when the pointer is this close to it (physical pixels).
const NEAR: f64 = 360.0;
/// After the button comes up, how long the window's drop event gets to arrive
/// and pin the zone before it is put away.
const DROP_GRACE: Duration = Duration::from_millis(350);

fn drag_pasteboard() -> objc2::rc::Retained<NSPasteboard> {
    // SAFETY: NSPasteboardNameDrag is a valid AppKit constant.
    unsafe { NSPasteboard::pasteboardWithName(NSPasteboardNameDrag) }
}

fn change_count() -> isize {
    drag_pasteboard().changeCount()
}

fn carries_files() -> bool {
    // Finder and most apps publish file URLs; older ones only the legacy
    // filenames type.
    let legacy = NSString::from_str("NSFilenamesPboardType");
    // SAFETY: NSPasteboardTypeFileURL is a valid AppKit constant.
    let wanted = NSArray::from_slice(&[unsafe { NSPasteboardTypeFileURL }, &*legacy]);
    drag_pasteboard().availableTypeFromArray(&wanted).is_some()
}

fn left_button_down() -> bool {
    NSEvent::pressedMouseButtons() & 1 != 0
}

fn option_down() -> bool {
    NSEvent::modifierFlags_class().contains(NSEventModifierFlags::Option)
}

/// Distance from the pointer to the drop zone's edge; 0 inside it.
fn distance_to_zone(app: &AppHandle) -> Option<f64> {
    let pointer = app.cursor_position().ok()?;
    let (x, y, width, height) = windows::dropzone_rect(app)?;
    let dx = (x - pointer.x).max(pointer.x - (x + width)).max(0.0);
    let dy = (y - pointer.y).max(pointer.y - (y + height)).max(0.0);
    Some(dx.hypot(dy))
}

/// One file drag, from the moment the zone is summoned until the button
/// comes up.
struct Drag {
    mode: &'static str,
    started: Instant,
    shake: Shake,
    /// Shaken away: stays hidden for the rest of this drag.
    dismissed: bool,
    visible: bool,
    compact: bool,
}

impl Drag {
    fn start(app: &AppHandle) -> Self {
        let shell = app.state::<Shell>();
        shell.drag_active.store(true, Ordering::SeqCst);
        let index = shell.drag_mode.load(Ordering::SeqCst) as usize;
        let mode = settings::DRAG_MODES.get(index).copied().unwrap_or("show");
        // A zone opened on purpose is left exactly as it is.
        let pinned = shell.pinned.load(Ordering::SeqCst);
        let mut drag = Self {
            mode: if pinned { "show" } else { mode },
            started: Instant::now(),
            shake: Shake::default(),
            dismissed: false,
            visible: false,
            compact: false,
        };
        if drag.mode == "small" {
            drag.set_compact(app, true);
        }
        drag.set_visible(app, drag.mode != "option" || !option_down());
        drag
    }

    fn set_visible(&mut self, app: &AppHandle, visible: bool) {
        if visible == self.visible {
            return;
        }
        self.visible = visible;
        if visible {
            windows::show_dropzone(app);
        } else {
            windows::hide_dropzone_window(app);
        }
    }

    fn set_compact(&mut self, app: &AppHandle, compact: bool) {
        if compact != self.compact {
            self.compact = compact;
            windows::set_dropzone_compact(app, compact);
        }
    }

    fn tick(&mut self, app: &AppHandle) {
        match self.mode {
            "option" => self.set_visible(app, !option_down()),
            "shake" if !self.dismissed => {
                let Ok(pointer) = app.cursor_position() else { return };
                if self.shake.feed(pointer.x, self.started.elapsed().as_millis() as u64) {
                    self.dismissed = true;
                    self.set_visible(app, false);
                }
            }
            "small" => {
                if let Some(distance) = distance_to_zone(app) {
                    self.set_compact(app, distance > NEAR);
                }
            }
            _ => {}
        }
    }

    fn end(mut self, app: &AppHandle) {
        // Give the window's drop event time to pin the zone.
        std::thread::sleep(DROP_GRACE);
        let shell = app.state::<Shell>();
        shell.drag_active.store(false, Ordering::SeqCst);
        if !shell.pinned.load(Ordering::SeqCst) {
            windows::close_dropzone(app);
        }
        // Whatever happened, the zone is full size the next time it is seen.
        self.set_compact(app, false);
    }
}

/// Starts the watcher thread; it lives as long as the app.
pub fn install(app: AppHandle) {
    std::thread::spawn(move || {
        // The change count of the last drag already dealt with. A drag that
        // ends is always marked as dealt with, so files left on the pasteboard
        // by an old drag can never summon the zone on a later plain click.
        let mut handled = change_count();
        let mut drag: Option<Drag> = None;
        loop {
            std::thread::sleep(if drag.is_some() { DRAG_POLL } else { POLL });
            if !left_button_down() {
                if let Some(ended) = drag.take() {
                    ended.end(&app);
                }
                handled = change_count();
                continue;
            }
            if let Some(current) = drag.as_mut() {
                current.tick(&app);
                continue;
            }
            if !app.state::<Shell>().dropzone_enabled.load(Ordering::SeqCst) {
                continue;
            }
            // Button is down: has a drag session started since the last one?
            // The types can lag the count by a tick, so an unhandled count is
            // re-examined until files show up or the button is released.
            let count = change_count();
            if count == handled || !carries_files() {
                continue;
            }
            handled = count;
            #[cfg(debug_assertions)]
            eprintln!("tomd: file drag detected (drag pasteboard change {count})");
            drag = Some(Drag::start(&app));
        }
    });
}
