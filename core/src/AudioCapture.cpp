#include "AudioCapture.hpp"

#include <algorithm>
#include <cmath>

namespace okcomputer {

std::expected<void, OkError> AudioCapture::Start(AudioCallback callback) {
  running_ = true;
  std::vector<int16_t> silence(480, 0);
  callback(std::span<const int16_t>(silence.data(), silence.size()));
  return {};
}

std::expected<void, OkError> AudioCapture::Stop() {
  running_ = false;
  return {};
}

std::vector<int16_t> AudioCapture::ConvertFloat32ToMonoPcm16(std::span<const float> frames, int channels) {
  const int safe_channels = std::max(1, channels);
  std::vector<int16_t> out;
  out.reserve(frames.size() / static_cast<size_t>(safe_channels));
  for (size_t i = 0; i < frames.size(); i += static_cast<size_t>(safe_channels)) {
    float mixed = 0.0F;
    for (int c = 0; c < safe_channels && i + static_cast<size_t>(c) < frames.size(); ++c) {
      mixed += frames[i + static_cast<size_t>(c)];
    }
    mixed /= static_cast<float>(safe_channels);
    const float clamped = std::clamp(mixed, -1.0F, 1.0F);
    out.push_back(static_cast<int16_t>(std::lrint(clamped * 32767.0F)));
  }
  return out;
}

} // namespace okcomputer
