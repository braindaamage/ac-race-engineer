import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { TabBar } from "./TabBar";
import { ToastContainer } from "./ToastContainer";
import "./AppShell.css";

export function AppShell() {
  return (
    <div className="ace-app-shell">
      <Header />
      <TabBar />
      <main className="ace-app-shell__content">
        <Outlet />
      </main>
      <ToastContainer />
    </div>
  );
}
