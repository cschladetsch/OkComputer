import React from "react";
import { createRoot } from "react-dom/client";
import { CommandPalette } from "./components/CommandPalette";
import { LLMStatus } from "./components/LLMStatus";
import { PrivacyBadge } from "./components/PrivacyBadge";
import { SettingsPanel } from "./components/SettingsPanel";
import { StopButton } from "./components/StopButton";
import { TranscriptFeed } from "./components/TranscriptFeed";
import { WakeWordStatus } from "./components/WakeWordStatus";
import { useOkComputerStore } from "./store/useOkComputerStore";
import "./style.css";

function App(): JSX.Element {
  const store = useOkComputerStore();
  React.useEffect(() => {
    store.connect();
  }, []);
  if (!store.connected) {
    return <main className="app"><WakeWordStatus state="IDLE" /></main>;
  }
  return (
    <main className="app">
      <PrivacyBadge privacyMode={store.privacyMode} />
      <StopButton onStop={() => store.sendCommand("STOP")} />
      <WakeWordStatus state={store.state} />
      <TranscriptFeed entries={store.transcripts} />
      <CommandPalette commands={store.commands} onCommand={store.sendCommand} />
      <LLMStatus status={store.llmStatus} />
      <SettingsPanel config={store.config} errors={store.validationErrors} onSave={store.saveConfig} onReload={store.reloadConfig} />
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(<App />);
