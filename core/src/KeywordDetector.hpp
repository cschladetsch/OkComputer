#pragma once

#include "OkComputer/Interfaces.hpp"

namespace okcomputer {

class KeywordDetector final : public IKeywordDetector {
public:
  std::expected<void, OkError> Start() override;
  std::expected<void, OkError> Stop() override;
  std::expected<void, OkError> AcceptPcm(std::span<const int16_t> frames) override;
  void OnCommandComplete() override;
  bool suppressed() const;

private:
  bool running_{false};
  bool suppressed_{false};
};

} // namespace okcomputer
