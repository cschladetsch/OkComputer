import type { CommandDefinition } from "../types";

export const commands: CommandDefinition[] = [
  { name: "Volume up", trigger_phrases: ["volume up", "louder", "turn it up"], action_enum: "VOLUME_UP", parameters: ["step"], confirmation_text: "Turning it up.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Volume down", trigger_phrases: ["volume down", "quieter", "turn it down"], action_enum: "VOLUME_DOWN", parameters: ["step"], confirmation_text: "Turning it down.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Mute", trigger_phrases: ["mute", "silence"], action_enum: "VOLUME_MUTE", parameters: [], confirmation_text: "Muting.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Unmute", trigger_phrases: ["unmute", "sound on"], action_enum: "VOLUME_UNMUTE", parameters: [], confirmation_text: "Sound on.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Pause media", trigger_phrases: ["pause", "stop music"], action_enum: "MEDIA_PAUSE", parameters: [], confirmation_text: "Pausing.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Resume media", trigger_phrases: ["resume", "play", "unpause"], action_enum: "MEDIA_RESUME", parameters: [], confirmation_text: "Playing.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Next track", trigger_phrases: ["next track", "skip"], action_enum: "MEDIA_NEXT", parameters: [], confirmation_text: "Skipping.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Previous track", trigger_phrases: ["previous track", "go back"], action_enum: "MEDIA_PREVIOUS", parameters: [], confirmation_text: "Going back.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Open app", trigger_phrases: ["open [app]", "launch [app]"], action_enum: "APP_OPEN", parameters: ["app"], confirmation_text: "Opening app.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Close app", trigger_phrases: ["close [app]", "quit [app]"], action_enum: "APP_CLOSE", parameters: ["app"], confirmation_text: "Closing app.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Screenshot", trigger_phrases: ["take a screenshot", "screenshot"], action_enum: "SCREENSHOT", parameters: ["path"], confirmation_text: "Taking a screenshot.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Privacy on", trigger_phrases: ["stop listening"], action_enum: "PRIVACY_MODE_ON", parameters: [], confirmation_text: "Privacy mode on.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Privacy off", trigger_phrases: ["start listening"], action_enum: "PRIVACY_MODE_OFF", parameters: [], confirmation_text: "Listening again.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Sleep", trigger_phrases: ["sleep", "go to sleep"], action_enum: "SYSTEM_SLEEP", parameters: [], confirmation_text: "Going to sleep.", platforms_supported: ["win32", "linux", "macos"] },
  { name: "Lock", trigger_phrases: ["lock", "lock the screen"], action_enum: "SYSTEM_LOCK", parameters: [], confirmation_text: "Locking.", platforms_supported: ["win32", "linux", "macos"] }
];
