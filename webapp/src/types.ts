export type AssistantState = "IDLE" | "LISTENING" | "PROCESSING" | "SPEAKING" | "PRIVACY";
export type Speaker = "USER" | "ASSISTANT";
export type ActionEnum =
  | "VOLUME_UP"
  | "VOLUME_DOWN"
  | "VOLUME_MUTE"
  | "VOLUME_UNMUTE"
  | "MEDIA_PAUSE"
  | "MEDIA_RESUME"
  | "MEDIA_NEXT"
  | "MEDIA_PREVIOUS"
  | "APP_OPEN"
  | "APP_CLOSE"
  | "SCREENSHOT"
  | "PRIVACY_MODE_ON"
  | "PRIVACY_MODE_OFF"
  | "SYSTEM_SLEEP"
  | "SYSTEM_LOCK"
  | "STOP";

export interface TranscriptEntry {
  utterance_id?: string;
  timestamp: string;
  speaker: Speaker;
  text: string;
  source?: "stt" | "tts";
  status?: "partial" | "complete" | "interrupted";
}

export interface CommandDefinition {
  name: string;
  trigger_phrases: string[];
  action_enum: ActionEnum;
  parameters: string[];
  confirmation_text: string;
  platforms_supported: string[];
}

export interface EndpointStatus {
  healthy: boolean;
  model: string;
  latency_ms: number | null;
}

export interface LLMStatusSnapshot {
  primary: EndpointStatus;
  fallback: EndpointStatus;
  latencies_ms: number[];
}

export interface OkConfig {
  version: string;
  wake_word: string;
  wake_word_sensitivity: number;
  [key: string]: unknown;
}

export type WSMessage =
  | { type: "state"; state: AssistantState }
  | { type: "transcript"; speaker: Speaker; text: string; timestamp: string }
  | { type: "transcript_delta"; speaker: "ASSISTANT"; utterance_id: string; sequence: number; text: string; final: boolean }
  | { type: "transcript_entry"; speaker: "ASSISTANT"; utterance_id: string; text: string; timestamp: string; source: "tts"; status: "complete" | "interrupted" }
  | { type: "llm_status"; primary: EndpointStatus; fallback: EndpointStatus; latencies_ms: number[] }
  | { type: "config"; config: OkConfig }
  | { type: "validation_error"; field: string; message: string }
  | { type: "error"; code: string; message: string; request_id?: string }
  | { type: "command"; action: "STOP" }
  | { type: "system_command"; action: ActionEnum; parameters: Record<string, unknown> }
  | { type: "config_update"; config: OkConfig }
  | { type: "reload_config" };

export interface WakeWordStatusProps {
  state: AssistantState;
}

export interface TranscriptFeedProps {
  entries: TranscriptEntry[];
}

export interface CommandPaletteProps {
  commands: CommandDefinition[];
  onCommand(action: ActionEnum): void;
}

export interface LLMStatusProps {
  status: LLMStatusSnapshot;
}

export interface SettingsPanelProps {
  config: OkConfig;
  errors: Record<string, string>;
  onSave(config: OkConfig): void;
  onReload(): void;
}

export interface PrivacyBadgeProps {
  privacyMode: boolean;
}

export interface StopButtonProps {
  onStop(): void;
}
