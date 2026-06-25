import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CommandPalette } from "../src/components/CommandPalette";
import { LLMStatus } from "../src/components/LLMStatus";
import { SettingsPanel } from "../src/components/SettingsPanel";
import { StopButton } from "../src/components/StopButton";
import { TranscriptFeed } from "../src/components/TranscriptFeed";
import { WakeWordStatus } from "../src/components/WakeWordStatus";
import { commands } from "../src/store/commands";

describe("components", () => {
  it("renders all wake states with aria labels", () => {
    for (const state of ["IDLE", "LISTENING", "PROCESSING", "SPEAKING", "PRIVACY"] as const) {
      const { unmount } = render(<WakeWordStatus state={state} />);
      expect(screen.getByRole("status")).toHaveAttribute("aria-label", state);
      unmount();
    }
  });

  it("renders transcript entries", () => {
    render(<TranscriptFeed entries={[{ timestamp: "now", speaker: "USER", text: "hello" }]} />);
    expect(screen.getByText("hello")).toBeInTheDocument();
  });

  it("filters and sends commands", () => {
    const onCommand = vi.fn();
    render(<CommandPalette commands={commands} onCommand={onCommand} />);
    fireEvent.change(screen.getByLabelText("Filter commands"), { target: { value: "louder" } });
    fireEvent.click(screen.getByText("Volume up"));
    expect(onCommand).toHaveBeenCalledWith("VOLUME_UP");
  });

  it("shows llm status and sparkline", () => {
    render(<LLMStatus status={{ primary: { healthy: true, model: "p", latency_ms: 1 }, fallback: { healthy: false, model: "f", latency_ms: null }, latencies_ms: [1, 2, 3, 4, 5] }} />);
    expect(screen.getByLabelText("Last 5 query latencies")).toBeInTheDocument();
  });

  it("saves settings and reloads", () => {
    const onSave = vi.fn();
    const onReload = vi.fn();
    render(<SettingsPanel config={{ version: "1", wake_word: "ok computer", wake_word_sensitivity: 0.5 }} errors={{ wake_word: "bad" }} onSave={onSave} onReload={onReload} />);
    expect(screen.getByText("bad")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Save"));
    fireEvent.click(screen.getByText("Reload Config"));
    expect(onSave).toHaveBeenCalled();
    expect(onReload).toHaveBeenCalled();
  });

  it("stop button sends stop", () => {
    const onStop = vi.fn();
    render(<StopButton onStop={onStop} />);
    fireEvent.click(screen.getByText("STOP"));
    expect(onStop).toHaveBeenCalled();
  });
});
