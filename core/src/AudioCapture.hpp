#pragma once

#include "OkComputer/Interfaces.hpp"

#include <vector>

namespace okcomputer {

class AudioCapture final : public IAudioCapture {
public:
  std::expected<void, OkError> Start(AudioCallback callback) override;
  std::expected<void, OkError> Stop() override;
  static std::vector<int16_t> ConvertFloat32ToMonoPcm16(std::span<const float> frames, int channels);

private:
  bool running_{false};
};

} // namespace okcomputer
