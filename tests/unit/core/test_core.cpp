#include "AudioCapture.hpp"
#include "CommandRouter.hpp"
#include "Config.hpp"
#include "IPCServer.hpp"
#include "KeywordDetector.hpp"
#include "StateMachine.hpp"
#include "TTSEngine.hpp"

#include <chrono>
#include <thread>

using namespace okcomputer;

namespace {

void Check(bool condition) {
  if (!condition) {
    std::terminate();
  }
}

} // namespace

int main() {
  Config config("okcomputer.config.json");
  Check(config.Load().has_value());
  Check(config.Get("wake_word").value() == "ok computer");

  const float samples[] = {1.0F, -1.0F, 0.5F, -0.5F};
  const auto pcm = AudioCapture::ConvertFloat32ToMonoPcm16(samples, 2);
  Check(pcm.size() == 2);
  Check(pcm[0] == 0);

  CommandRouter router;
  auto route = router.Route("ok computer volume up");
  Check(route.has_value());
  Check(route->action == Action::VolumeUp);

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
  machine.AddStopHandler([&stopped]() {
    stopped = true;
    return std::expected<void, OkError>{};
  });
  Check(machine.Transition(State::Speaking).has_value());
  Check(machine.Stop().has_value());
  Check(stopped);
  Check(machine.CurrentState() == State::Idle);

  const auto before = std::chrono::steady_clock::now();
  Config missing("__missing_config__.json");
  Check(!missing.Load().has_value());
  const auto elapsed = std::chrono::steady_clock::now() - before;
  Check(elapsed >= std::chrono::milliseconds(50));

  return 0;
}
