#include "AudioCapture.hpp"
#include "CommandRouter.hpp"
#include "Config.hpp"
#include "IPCServer.hpp"
#include "KeywordDetector.hpp"
#include "StateMachine.hpp"
#include "TTSEngine.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <string>
#include <thread>

using namespace okcomputer;

namespace {

void Check(bool condition) {
  if (!condition) {
    std::terminate();
  }
}

std::filesystem::path TempPath(std::string_view name) {
  return std::filesystem::temp_directory_path() / std::string(name);
}

void WriteText(const std::filesystem::path& path, std::string_view text) {
  std::ofstream out(path, std::ios::trunc);
  out << text;
}

} // namespace

int main() {
  Config config("okcomputer.config.json");
  Check(config.Load().has_value());
  Check(config.Get("wake_word").value() == "ok computer");
  Check(config.Get("audio.sample_rate").value() == "16000");

  const auto config_path = TempPath("okcomputer_core_config_test.json");
  WriteText(config_path, R"({"version":"1","wake_word":"computer","audio":{"sample_rate":22050}})");
  Config temp_config(config_path);
  Check(temp_config.Load().has_value());
  Check(temp_config.Get("wake_word").value() == "computer");
  Check(temp_config.Get("audio.sample_rate").value() == "22050");
  Check(temp_config.Get("ipc.ws_port").value() == "5003");
  WriteText(config_path, R"({"version":"1","wake_word":"new computer","audio":{"sample_rate":44100}})");
  Check(temp_config.Watch().has_value());
  Check(temp_config.Get("wake_word").value() == "new computer");
  WriteText(config_path, R"({"version":"1","wake_word":)");
  Check(!temp_config.Load().has_value());
  Check(temp_config.Get("wake_word").value() == "new computer");

  const float samples[] = {1.0F, -1.0F, 0.5F, -0.5F};
  const auto pcm = AudioCapture::ConvertFloat32ToMonoPcm16(samples, 2);
  Check(pcm.size() == 2);
  Check(pcm[0] == 0);

  CommandRouter router;
  auto route = router.Route("ok computer volume up");
  Check(route.has_value());
  Check(route->action == Action::VolumeUp);
  Check(router.Route("volum up")->action == Action::VolumeUp);
  Check(router.Route("quieter")->action == Action::VolumeDown);
  Check(router.Route("silence")->action == Action::VolumeMute);
  Check(router.Route("sound on")->action == Action::VolumeUnmute);
  Check(router.Route("pause")->action == Action::MediaPause);
  Check(router.Route("play")->action == Action::MediaResume);
  Check(router.Route("skip")->action == Action::MediaNext);
  Check(router.Route("go back")->action == Action::MediaPrevious);
  Check(router.Route("open notepad")->action == Action::AppOpen);
  Check(router.Route("quit notepad")->action == Action::AppClose);
  Check(router.Route("take a screenshot")->action == Action::Screenshot);
  Check(router.Route("stop listening")->action == Action::PrivacyModeOn);
  Check(router.Route("start listening")->action == Action::PrivacyModeOff);
  Check(router.Route("go to sleep")->action == Action::SystemSleep);
  Check(router.Route("lock the screen")->action == Action::SystemLock);
  Check(router.Route("what is the capital of france")->action == Action::GeneralQuery);

  KeywordDetector detector;
  Check(detector.Start().has_value());
  const int16_t frame[] = {1, 2, 3};
  Check(detector.AcceptPcm(frame).has_value());
  Check(detector.suppressed());
  detector.OnCommandComplete();
  Check(!detector.suppressed());

  TTSEngine tts;
  Check(tts.Speak("hello").has_value());
  Check(tts.last_text() == "hello");
  Check(tts.Interrupt().has_value());
  Check(tts.interrupted());

  IPCServer ipc;
  Check(!ipc.SendJson("{}").has_value());
  Check(ipc.Start().has_value());
  Check(ipc.SendJson("{\"type\":\"ping\"}").has_value());
  Check(ipc.sent().size() == 1);

  StateMachine machine;
  bool stopped = false;
  bool second_stopped = false;
  machine.AddStopHandler([&stopped]() {
    stopped = true;
    return std::unexpected(OkError{"STOP_TIMEOUT", "first handler failed"});
  });
  machine.AddStopHandler([&second_stopped]() {
    second_stopped = true;
    return std::expected<void, OkError>{};
  });
  Check(machine.Transition(State::Speaking).has_value());
  Check(!machine.Stop().has_value());
  Check(stopped);
  Check(second_stopped);
  Check(machine.CurrentState() == State::Idle);

  const auto before = std::chrono::steady_clock::now();
  Config missing("__missing_config__.json");
  Check(!missing.Load().has_value());
  const auto elapsed = std::chrono::steady_clock::now() - before;
  Check(elapsed >= std::chrono::milliseconds(50));

  return 0;
}
