//! The Python sidecar (`sidecar.py`): one JSON request per stdin line, JSON
//! events back on stdout. This module only moves lines; the webview matches
//! replies to requests by id (`src/ipc.ts`).

use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::Mutex;

use tauri::{AppHandle, Emitter, Manager, State};

pub struct Sidecar {
    child: Mutex<Option<Child>>,
    stdin: Mutex<Option<ChildStdin>>,
}

/// Debug builds run the source with the project's venv; release builds run the
/// frozen sidecar shipped in the app's resources.
fn command(app: &AppHandle) -> Command {
    if cfg!(debug_assertions) {
        let repo = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
        let mut cmd = Command::new(repo.join(".venv/bin/python"));
        cmd.arg(repo.join("sidecar.py"));
        cmd
    } else {
        let dir = app.path().resource_dir().unwrap_or_default();
        Command::new(dir.join("sidecar/tomd-sidecar"))
    }
}

impl Sidecar {
    pub fn spawn(app: &AppHandle) -> Self {
        let spawned = command(app)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn();
        let mut child = match spawned {
            Ok(child) => child,
            Err(err) => {
                eprintln!("tomd: could not start the sidecar: {err}");
                return Self { child: Mutex::new(None), stdin: Mutex::new(None) };
            }
        };
        let stdin = child.stdin.take();
        if let Some(stdout) = child.stdout.take() {
            let app = app.clone();
            std::thread::spawn(move || {
                for line in BufReader::new(stdout).lines().map_while(Result::ok) {
                    let _ = app.emit("sidecar-message", line);
                }
            });
        }
        Self { child: Mutex::new(Some(child)), stdin: Mutex::new(stdin) }
    }

    pub fn kill(&self) {
        if let Some(mut child) = self.child.lock().unwrap().take() {
            let _ = child.kill();
        }
    }
}

#[tauri::command]
pub fn sidecar_send(state: State<Sidecar>, line: String) -> Result<(), String> {
    if line.contains('\n') {
        return Err("A request must be a single line".into());
    }
    let mut guard = state.stdin.lock().unwrap();
    let stdin = guard.as_mut().ok_or("The conversion backend isn't running")?;
    writeln!(stdin, "{line}").and_then(|_| stdin.flush()).map_err(|e| e.to_string())
}
