import { Outlet } from "react-router-dom";
import "./SessionLayout.css";

export function SessionLayout() {
  return (
    <div className="ace-session-layout">
      <Outlet />
    </div>
  );
}
