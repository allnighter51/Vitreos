// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Child};
use std::sync::Mutex;

struct AppState {
    python_process: Mutex<Option<Child>>,
}

#[tauri::command]
fn start_sentinel_server(state: tauri::State<AppState>) -> Result<String, String> {
    let mut process_guard = state.python_process.lock().unwrap();
    
    if process_guard.is_some() {
        return Ok("Server already running".to_string());
    }

    // Start Python WebSocket server
    let child = Command::new("python")
        .arg("vitreos_sentinel_server.py")
        .spawn()
        .map_err(|e| format!("Failed to start Python server: {}", e))?;

    *process_guard = Some(child);
    Ok("Sentinel server started".to_string())
}

#[tauri::command]
fn stop_sentinel_server(state: tauri::State<AppState>) -> Result<String, String> {
    let mut process_guard = state.python_process.lock().unwrap();
    
    if let Some(mut child) = process_guard.take() {
        child.kill().map_err(|e| format!("Failed to stop server: {}", e))?;
        Ok("Sentinel server stopped".to_string())
    } else {
        Ok("Server not running".to_string())
    }
}

fn main() {
    tauri::Builder::default()
        .manage(AppState {
            python_process: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            start_sentinel_server,
            stop_sentinel_server
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
