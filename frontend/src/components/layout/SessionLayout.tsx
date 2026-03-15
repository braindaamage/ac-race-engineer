import { Outlet } from "react-router-dom";
import { SessionHeader } from "./SessionHeader";
import "./SessionLayout.css";

export function SessionLayout() {
  return (
    <div className="ace-session-layout">
      <SessionHeader />
      <div className="ace-session-layout__content">
        <Outlet />
      </div>
    </div>
  );
}
