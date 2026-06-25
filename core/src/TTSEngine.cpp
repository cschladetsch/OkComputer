#include "TTSEngine.hpp"

namespace okcomputer {

std::expected<void, OkError> TTSEngine::Speak(std::string_view text) {
  last_text_ = text;
  interrupted_ = false;
  return {};
}

std::expected<void, OkError> TTSEngine::Interrupt() {
  interrupted_ = true;
  return {};
}

const std::string& TTSEngine::last_text() const { return last_text_; }

bool TTSEngine::interrupted() const { return interrupted_; }

} // namespace okcomputer
