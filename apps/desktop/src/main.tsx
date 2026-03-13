import React from "react";
import ReactDOM from "react-dom/client";
import { isTauri } from "@tauri-apps/api/core";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import App from "./App";
import Launcher from "./Launcher";
import "./styles.css";

const rootElement = document.getElementById("root");
const windowLabel = isTauri() ? getCurrentWebviewWindow().label : "settings";

document.documentElement.dataset.window = windowLabel;
document.body.dataset.window = windowLabel;
rootElement?.setAttribute("data-window", windowLabel);

const RootComponent = windowLabel === "search" ? Launcher : App;

ReactDOM.createRoot(rootElement!).render(
  <React.StrictMode>
    <RootComponent />
  </React.StrictMode>
);
