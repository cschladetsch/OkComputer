import { create } from "zustand";
import { commands } from "./commands";
import type { ActionEnum, AssistantState, CommandDefinition, LLMStatusSnapshot, OkConfig, TranscriptEntry, WSMessage } from "../types";

export interface OkComputerStore {
  connected: boolean;
  state: AssistantState;
  privacyMode: boolean;
  transcripts: TranscriptEntry[];
  config: OkConfig;
  commands: CommandDefinition[];
  llmStatus: LLMStatusSnapshot;
  validationErrors: Record<string, string>;
  connect(): void;
  handleMessage(message: WSMessage): void;
  sendCommand(action: ActionEnum): void;
  saveConfig(config: OkConfig): void;
  reloadConfig(): void;
}

const defaultStatus: LLMStatusSnapshot = {
  primary: { healthy: false, model: "qwen2.5-coder:7b", latency_ms: null },
  fallback: { healthy: false, model: "llama3.2:3b", latency_ms: null },
  latencies_ms: []
};

let socket: WebSocket | null = null;

function appendDeltaText(existing: string, delta: string): string {
  if (!existing) {
    return delta;
  }
  return `${existing} ${delta}`.replace(/\s+/g, " ").trim();
}

function send(message: WSMessage): void {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
}

export const useOkComputerStore = create<OkComputerStore>((set) => ({
  connected: false,
  state: "IDLE",
  privacyMode: false,
  transcripts: [],
  config: { version: "1", wake_word: "ok computer", wake_word_sensitivity: 0.5 },
  commands,
  llmStatus: defaultStatus,
  validationErrors: {},
  connect: () => {
    socket = new WebSocket(`ws://${window.location.hostname}:5003`);
    socket.onopen = () => set({ connected: true });
    socket.onclose = () => set({ connected: false });
    socket.onmessage = (event: MessageEvent<string>) => {
      const message = JSON.parse(event.data) as WSMessage;
      useOkComputerStore.getState().handleMessage(message);
    };
  },
  handleMessage: (message: WSMessage) => {
    if (message.type === "state") {
      set({ state: message.state, privacyMode: message.state === "PRIVACY" });
    } else if (message.type === "transcript") {
      set((state) => ({ transcripts: [...state.transcripts, { timestamp: message.timestamp, speaker: message.speaker, text: message.text }] }));
    } else if (message.type === "transcript_delta") {
      set((state) => {
        const existingIndex = state.transcripts.findIndex((entry) => entry.utterance_id === message.utterance_id);
        if (existingIndex === -1) {
          return {
            transcripts: [
              ...state.transcripts,
              {
                utterance_id: message.utterance_id,
                timestamp: new Date().toISOString(),
                speaker: message.speaker,
                text: message.text,
                source: "tts",
                status: message.final ? "complete" : "partial"
              }
            ]
          };
        }
        const transcripts = [...state.transcripts];
        const existing = transcripts[existingIndex];
        transcripts[existingIndex] = {
          ...existing,
          text: appendDeltaText(existing.text, message.text),
          status: message.final ? "complete" : "partial"
        };
        return { transcripts };
      });
    } else if (message.type === "transcript_entry") {
      set((state) => {
        const finalEntry: TranscriptEntry = {
          utterance_id: message.utterance_id,
          timestamp: message.timestamp,
          speaker: message.speaker,
          text: message.text,
          source: message.source,
          status: message.status
        };
        const existingIndex = state.transcripts.findIndex((entry) => entry.utterance_id === message.utterance_id);
        if (existingIndex === -1) {
          return { transcripts: [...state.transcripts, finalEntry] };
        }
        const transcripts = [...state.transcripts];
        transcripts[existingIndex] = finalEntry;
        return { transcripts };
      });
    } else if (message.type === "llm_status") {
      set({ llmStatus: { primary: message.primary, fallback: message.fallback, latencies_ms: message.latencies_ms.slice(-5) } });
    } else if (message.type === "config") {
      set({ config: message.config });
    } else if (message.type === "validation_error") {
      set((state) => ({ validationErrors: { ...state.validationErrors, [message.field]: message.message } }));
    }
  },
  sendCommand: (action: ActionEnum) => {
    if (action === "STOP") {
      send({ type: "command", action: "STOP" });
    } else {
      send({ type: "system_command", action, parameters: {} });
    }
  },
  saveConfig: (config: OkConfig) => send({ type: "config_update", config }),
  reloadConfig: () => send({ type: "reload_config" })
}));
