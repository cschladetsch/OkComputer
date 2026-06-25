#pragma once

#include "OkComputer/Interfaces.hpp"

#include <string>

namespace okcomputer {

class TTSEngine final : public ITTSEngine {
public:
  std::expected<void, OkError> Speak(std::string_view text) override;
  std::expected<void, OkError> Interrupt() override;
  const std::string& last_text() const;
  bool interrupted() const;

private:
  std::string last_text_;
  bool interrupted_{false};
};

} // namespace okcomputer
