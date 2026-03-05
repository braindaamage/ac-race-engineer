import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  Sidebar,
  NAVIGATION_SECTIONS,
} from "../../../src/components/layout/Sidebar";
import { useUIStore } from "../../../src/store/uiStore";
import { useSessionStore } from "../../../src/store/sessionStore";

describe("Sidebar", () => {
  beforeEach(() => {
    useUIStore.setState({
      activeSection: "sessions",
      sidebarCollapsed: false,
    });
    useSessionStore.setState({ selectedSessionId: null });
  });

  it("renders all nav items", () => {
    render(<Sidebar />);
    for (const section of NAVIGATION_SECTIONS) {
      expect(screen.getByText(section.label)).toBeInTheDocument();
    }
    expect(NAVIGATION_SECTIONS).toHaveLength(5);
  });

  it("clicking an item updates active section", () => {
    render(<Sidebar />);
    fireEvent.click(screen.getByText("Engineer"));
    expect(useUIStore.getState().activeSection).toBe("engineer");
  });

  it("active item has active class", () => {
    useUIStore.setState({ activeSection: "settings" });
    const { container } = render(<Sidebar />);
    const activeItems = container.querySelectorAll(
      ".ace-sidebar__item--active",
    );
    expect(activeItems).toHaveLength(1);
    expect(activeItems[0]!.textContent).toContain("Settings");
  });

  it("session-dependent items are dimmed when no session is selected", () => {
    const { container } = render(<Sidebar />);
    const dimmedItems = container.querySelectorAll(".ace-sidebar__item--dimmed");
    const sessionDependentCount = NAVIGATION_SECTIONS.filter(
      (s) => s.requiresSession,
    ).length;
    expect(dimmedItems).toHaveLength(sessionDependentCount);
  });

  it("session-dependent items are NOT dimmed when session is selected", () => {
    useSessionStore.setState({ selectedSessionId: "test-123" });
    const { container } = render(<Sidebar />);
    const dimmedItems = container.querySelectorAll(".ace-sidebar__item--dimmed");
    expect(dimmedItems).toHaveLength(0);
  });

  it("renders in dark theme", () => {
    const { container } = render(
      <div data-theme="dark">
        <Sidebar />
      </div>,
    );
    expect(container.querySelector(".ace-sidebar")).toBeInTheDocument();
  });

  it("renders in light theme", () => {
    const { container } = render(
      <div data-theme="light">
        <Sidebar />
      </div>,
    );
    expect(container.querySelector(".ace-sidebar")).toBeInTheDocument();
  });
});
