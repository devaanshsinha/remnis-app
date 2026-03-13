#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{Error as IoError, ErrorKind};

use tauri::{
    AppHandle, Emitter, Manager, WebviewWindow, WebviewWindowBuilder, WindowEvent,
};
use tauri_plugin_global_shortcut::{Builder as GlobalShortcutBuilder, ShortcutState};

const SEARCH_WINDOW_LABEL: &str = "search";
const SETTINGS_WINDOW_LABEL: &str = "settings";
const FOCUS_INPUT_EVENT: &str = "launcher:focus-input";
const LAUNCHER_SHORTCUT: &str = "Alt+Space";

#[cfg(target_os = "macos")]
fn configure_launcher_app_mode(app: &AppHandle) -> tauri::Result<()> {
    app.set_activation_policy(tauri::ActivationPolicy::Accessory)?;
    app.set_dock_visibility(false)?;
    Ok(())
}

#[cfg(not(target_os = "macos"))]
fn configure_launcher_app_mode(_app: &AppHandle) -> tauri::Result<()> {
    Ok(())
}

#[cfg(target_os = "macos")]
fn show_app(app: &AppHandle) -> tauri::Result<()> {
    app.show()
}

#[cfg(not(target_os = "macos"))]
fn show_app(_app: &AppHandle) -> tauri::Result<()> {
    Ok(())
}

fn window_config(
    app: &AppHandle,
    label: &str,
) -> tauri::Result<tauri::utils::config::WindowConfig> {
    app.config()
        .app
        .windows
        .iter()
        .find(|window| window.label == label)
        .cloned()
        .ok_or_else(|| IoError::new(ErrorKind::NotFound, format!("window config not found: {label}")))
        .map_err(Into::into)
}

fn bind_search_window_events(window: &WebviewWindow) {
    let search_window = window.clone();
    window.on_window_event(move |event| {
        match event {
            WindowEvent::CloseRequested { api, .. } => {
                api.prevent_close();
                let _ = search_window.hide();
            }
            WindowEvent::Focused(false) => {
                let _ = search_window.hide();
            }
            _ => {}
        }
    });
}

fn ensure_window(app: &AppHandle, label: &str) -> tauri::Result<WebviewWindow> {
    if let Some(window) = app.get_webview_window(label) {
        return Ok(window);
    }

    let config = window_config(app, label)?;
    let window = WebviewWindowBuilder::from_config(app, &config)?.build()?;
    if label == SEARCH_WINDOW_LABEL {
        bind_search_window_events(&window);
    }
    Ok(window)
}

fn emit_launcher_focus(window: &WebviewWindow) {
    let _ = window.emit(FOCUS_INPUT_EVENT, ());
}

fn show_search_window(app: &AppHandle) -> tauri::Result<()> {
    show_app(app)?;
    let window = ensure_window(app, SEARCH_WINDOW_LABEL)?;
    window.show()?;
    window.set_focus()?;
    emit_launcher_focus(&window);
    Ok(())
}

fn hide_search_window(app: &AppHandle) -> tauri::Result<()> {
    if let Some(window) = app.get_webview_window(SEARCH_WINDOW_LABEL) {
        window.hide()?;
    }
    Ok(())
}

fn toggle_search_window(app: &AppHandle) -> tauri::Result<()> {
    let window = ensure_window(app, SEARCH_WINDOW_LABEL)?;
    if window.is_visible()? {
        window.hide()?;
        return Ok(());
    }

    show_search_window(app)
}

fn open_settings_window(app: &AppHandle) -> tauri::Result<()> {
    show_app(app)?;
    let window = ensure_window(app, SETTINGS_WINDOW_LABEL)?;
    window.show()?;
    window.set_focus()?;
    Ok(())
}

#[tauri::command]
fn hide_search(app: AppHandle) -> Result<(), String> {
    hide_search_window(&app).map_err(|error| error.to_string())
}

#[tauri::command]
fn open_settings(app: AppHandle) -> Result<(), String> {
    hide_search_window(&app).map_err(|error| error.to_string())?;
    open_settings_window(&app).map_err(|error| error.to_string())
}

fn main() {
    let global_shortcut_plugin = GlobalShortcutBuilder::new()
        .with_shortcut(LAUNCHER_SHORTCUT)
        .expect("launcher shortcut must be valid")
        .with_handler(|app, _shortcut, event| {
            if event.state == ShortcutState::Pressed {
                let _ = toggle_search_window(app);
            }
        })
        .build();

    tauri::Builder::default()
        .plugin(global_shortcut_plugin)
        .invoke_handler(tauri::generate_handler![hide_search, open_settings])
        .setup(|app| {
            configure_launcher_app_mode(app.handle())?;
            if let Some(search_window) = app.get_webview_window(SEARCH_WINDOW_LABEL) {
                bind_search_window_events(&search_window);
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
