#pragma once

#include <cstdint>
#include <expected>
#include <functional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace okcomputer {

enum class State { Idle, Listening, Processing, Speaking, Privacy, Suppressed };

enum class Action {
  VolumeUp,
  VolumeDown,
  VolumeMute,
  VolumeUnmute,
  MediaPause,
  MediaResume,
  MediaNext,
  MediaPrevious,
  AppOpen,
  AppClose,
  Screenshot,
  PrivacyModeOn,
  PrivacyModeOff,
  SystemSleep,
  SystemLock,
  Stop,
  GeneralQuery
};

struct OkError {
  std::string code;
  std::string message;
};

struct RouteResult {
  Action action{Action::GeneralQuery};
  std::string text;
  bool requires_confirmation{false};
};

using AudioCallback = std::function<void(std::span<const int16_t>)>;
using StopHandler = std::function<std::expected<void, OkError>()>;

class IKeywordDetector {
public:
  virtual ~IKeywordDetector() = default;
  virtual std::expected<void, OkError> Start() = 0;
  virtual std::expected<void, OkError> Stop() = 0;
  virtual std::expected<void, OkError> AcceptPcm(std::span<const int16_t> frames) = 0;
  virtual void OnCommandComplete() = 0;
};

class ICommandRouter {
public:
  virtual ~ICommandRouter() = default;
  virtual std::expected<RouteResult, OkError> Route(std::string_view text) = 0;
  virtual std::expected<void, OkError> ResetConversation() = 0;
};

class ITTSEngine {
public:
  virtual ~ITTSEngine() = default;
  virtual std::expected<void, OkError> Speak(std::string_view text) = 0;
  virtual std::expected<void, OkError> Interrupt() = 0;
};

class IIPCServer {
public:
  virtual ~IIPCServer() = default;
  virtual std::expected<void, OkError> Start() = 0;
  virtual std::expected<void, OkError> Stop() = 0;
  virtual std::expected<void, OkError> SendJson(std::string_view frame) = 0;
};

class IConfigLoader {
public:
  virtual ~IConfigLoader() = default;
  virtual std::expected<void, OkError> Load() = 0;
  virtual std::expected<void, OkError> Watch() = 0;
  virtual std::expected<std::string, OkError> Get(std::string_view key) const = 0;
};

class IAudioCapture {
public:
  virtual ~IAudioCapture() = default;
  virtual std::expected<void, OkError> Start(AudioCallback callback) = 0;
  virtual std::expected<void, OkError> Stop() = 0;
};

class IStateMachine {
public:
  virtual ~IStateMachine() = default;
  virtual std::expected<void, OkError> Transition(State state) = 0;
  virtual std::expected<void, OkError> Stop() = 0;
  virtual State CurrentState() const = 0;
};

} // namespace okcomputer
