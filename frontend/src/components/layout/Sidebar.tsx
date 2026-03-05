import { useUIStore } from "../../store/uiStore";
import { useSessionStore } from "../../store/sessionStore";
import "./Sidebar.css";

interface NavSection {
  id: string;
  label: string;
  icon: string;
  requiresSession: boolean;
}

const NAVIGATION_SECTIONS: NavSection[] = [
  { id: "sessions", label: "Sessions", icon: "\u{1F4CB}", requiresSession: false },
  { id: "analysis", label: "Lap Analysis", icon: "\u{1F4CA}", requiresSession: true },
  { id: "compare", label: "Setup Compare", icon: "\u{1F504}", requiresSession: true },
  { id: "engineer", label: "Engineer", icon: "\u{1F916}", requiresSession: true },
  { id: "settings", label: "Settings", icon: "\u2699\uFE0F", requiresSession: false },
];

export { NAVIGATION_SECTIONS };

export function Sidebar() {
  const activeSection = useUIStore((s) => s.activeSection);
  const setActiveSection = useUIStore((s) => s.setActiveSection);
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId);

  return (
    <nav
      className={`ace-sidebar${sidebarCollapsed ? " ace-sidebar--collapsed" : ""}`}
    >
      <button className="ace-sidebar__logo" onClick={toggleSidebar}>
        AC RE
      </button>
      <ul className="ace-sidebar__nav">
        {NAVIGATION_SECTIONS.map((section) => {
          const isDimmed =
            section.requiresSession && selectedSessionId === null;
          const isActive = activeSection === section.id;

          return (
            <li key={section.id}>
              <button
                className={`ace-sidebar__item${isActive ? " ace-sidebar__item--active" : ""}${isDimmed ? " ace-sidebar__item--dimmed" : ""}`}
                onClick={() => setActiveSection(section.id)}
              >
                <span className="ace-sidebar__icon">{section.icon}</span>
                {!sidebarCollapsed && (
                  <span className="ace-sidebar__label">{section.label}</span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
