import { useState } from "react";
import type { SettingsPanelProps } from "../types";

export function SettingsPanel({ config, errors, onSave, onReload }: SettingsPanelProps): JSX.Element {
  const [draft, setDraft] = useState(config);
  const update = (key: string, value: string | number): void => setDraft((current) => ({ ...current, [key]: value }));
  return (
    <section className="panel settings">
      <label>Wake word<input value={String(draft.wake_word)} onChange={(event) => update("wake_word", event.target.value)} /></label>
      {errors.wake_word ? <span className="error">{errors.wake_word}</span> : null}
      <label>Sensitivity<input type="number" step="0.1" value={Number(draft.wake_word_sensitivity)} onChange={(event) => update("wake_word_sensitivity", Number(event.target.value))} /></label>
      {errors.wake_word_sensitivity ? <span className="error">{errors.wake_word_sensitivity}</span> : null}
      <button type="button" onClick={() => onSave(draft)}>Save</button>
      <button type="button" onClick={onReload}>Reload Config</button>
    </section>
  );
}
