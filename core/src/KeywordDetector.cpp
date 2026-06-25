#include "KeywordDetector.hpp"

namespace okcomputer {

std::expected<void, OkError> KeywordDetector::Start() {
  running_ = true;
  suppressed_ = false;
  return {};
}

std::expected<void, OkError> KeywordDetector::Stop() {
  running_ = false;
  return {};
}

std::expected<void, OkError> KeywordDetector::AcceptPcm(std::span<const int16_t> frames) {
  if (!running_ || suppressed_ || frames.empty()) {
    return {};
  }
  suppressed_ = true;
  return {};
}

void KeywordDetector::OnCommandComplete() { suppressed_ = false; }

bool KeywordDetector::suppressed() const { return suppressed_; }

} // namespace okcomputer
