import { Card } from "../../components/ui";
import { Button } from "../../components/ui";
import { useTheme } from "../../hooks/useTheme";

export function SettingsView() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div style={{ padding: "var(--space-6)" }}>
      <Card title="Settings">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>Theme</span>
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            <Button
              variant={theme === "dark" ? "primary" : "secondary"}
              size="sm"
              onClick={() => {
                if (theme !== "dark") toggleTheme();
              }}
            >
              Night Grid
            </Button>
            <Button
              variant={theme === "light" ? "primary" : "secondary"}
              size="sm"
              onClick={() => {
                if (theme !== "light") toggleTheme();
              }}
            >
              Garage Floor
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
