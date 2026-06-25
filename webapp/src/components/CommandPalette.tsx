import { useMemo, useState } from "react";
import type { CommandPaletteProps } from "../types";

export function CommandPalette({ commands, onCommand }: CommandPaletteProps): JSX.Element {
  const [filter, setFilter] = useState("");
  const visible = useMemo(
    () => commands.filter((command) => `${command.name} ${command.trigger_phrases.join(" ")}`.toLowerCase().includes(filter.toLowerCase())),
    [commands, filter]
  );
  return (
    <section className="panel">
      <input aria-label="Filter commands" value={filter} onChange={(event) => setFilter(event.target.value)} />
      <div className="command-list">
        {visible.map((command) => (
          <button key={command.action_enum} type="button" onClick={() => onCommand(command.action_enum)}>
            <span>{command.name}</span>
            <small>{command.trigger_phrases.join(", ")}</small>
          </button>
        ))}
      </div>
    </section>
  );
}
