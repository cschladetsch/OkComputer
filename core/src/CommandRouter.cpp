#include "CommandRouter.hpp"

#include <algorithm>
#include <cctype>
#include <string>

namespace okcomputer {
namespace {

std::string Lower(std::string_view text) {
  std::string out(text);
  std::ranges::transform(out, out.begin(), [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
  return out;
}

bool Contains(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

} // namespace

std::expected<RouteResult, OkError> CommandRouter::Route(std::string_view text) {
  std::string normalized = Lower(text);
  if (normalized.starts_with("ok computer ")) {
    normalized.erase(0, 12);
  }
  if (Contains(normalized, "volume up") || Contains(normalized, "louder") || Contains(normalized, "turn it up")) {
    return RouteResult{Action::VolumeUp, normalized, true};
  }
  if (Contains(normalized, "volume down") || Contains(normalized, "quieter") || Contains(normalized, "turn it down")) {
    return RouteResult{Action::VolumeDown, normalized, true};
  }
  if (Contains(normalized, "mute") && !Contains(normalized, "unmute")) {
    return RouteResult{Action::VolumeMute, normalized, true};
  }
  if (Contains(normalized, "unmute") || Contains(normalized, "sound on")) {
    return RouteResult{Action::VolumeUnmute, normalized, true};
  }
  if (Contains(normalized, "stop listening")) {
    return RouteResult{Action::PrivacyModeOn, normalized, false};
  }
  if (Contains(normalized, "start listening")) {
    return RouteResult{Action::PrivacyModeOff, normalized, false};
  }
  if (Contains(normalized, "stop")) {
    return RouteResult{Action::Stop, normalized, false};
  }
  return RouteResult{Action::GeneralQuery, normalized, false};
}

std::expected<void, OkError> CommandRouter::ResetConversation() { return {}; }

} // namespace okcomputer
