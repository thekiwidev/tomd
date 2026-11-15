import React from "react";
import ReactDOM from "react-dom/client";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { DropZone } from "./DropZone";
import { MainWindow } from "./MainWindow";
import { Toast } from "./Toast";
import "./app.css";

const Root = { dropzone: DropZone, toast: Toast }[getCurrentWindow().label] ?? MainWindow;

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
);
