#include "CommandRouter.hpp"

#include <algorithm>
#include <cctype>
#include <string>
#include <vector>

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

int Levenshtein(std::string_view left, std::string_view right) {
  std::vector<int> previous(right.size() + 1);
  std::vector<int> current(right.size() + 1);
  for (size_t j = 0; j <= right.size(); ++j) {
    previous[j] = static_cast<int>(j);
  }
  for (size_t i = 1; i <= left.size(); ++i) {
    current[0] = static_cast<int>(i);
    for (size_t j = 1; j <= right.size(); ++j) {
      const int substitution = previous[j - 1] + (left[i - 1] == right[j - 1] ? 0 : 1);
      const int insertion = current[j - 1] + 1;
      const int deletion = previous[j] + 1;
      current[j] = std::min({substitution, insertion, deletion});
    }
    previous.swap(current);
  }
  return previous[right.size()];
}

bool Matches(std::string_view text, const std::vector<std::string_view>& triggers) {
  for (const auto trigger : triggers) {
    if (Contains(text, trigger) || Levenshtein(text, trigger) <= 2) {
      return true;
    }
  }
  return false;
}

std::string StripWakeWord(std::string normalized) {
  constexpr std::string_view wake_word = "ok computer";
  if (normalized == wake_word) {
    return {};
  }
  if (normalized.starts_with("ok computer ")) {
    normalized.erase(0, wake_word.size() + 1);
  }
  return normalized;
}

} // namespace

std::expected<RouteResult, OkError> CommandRouter::Route(std::string_view text) {
  const std::string normalized = StripWakeWord(Lower(text));
  if (Matches(normalized, {"volume up", "louder", "turn it up"})) {
    return RouteResult{Action::VolumeUp, normalized, true};
  }
  if (Matches(normalized, {"volume down", "quieter", "turn it down"})) {
    return RouteResult{Action::VolumeDown, normalized, true};
  }
  if (Matches(normalized, {"mute", "silence"}) && !Matches(normalized, {"unmute"})) {
    return RouteResult{Action::VolumeMute, normalized, true};
  }
  if (Matches(normalized, {"unmute", "sound on"})) {
    return RouteResult{Action::VolumeUnmute, normalized, true};
  }
  if (Matches(normalized, {"pause", "stop music"})) {
    return RouteResult{Action::MediaPause, normalized, true};
  }
  if (Matches(normalized, {"resume", "play", "unpause"})) {
    return RouteResult{Action::MediaResume, normalized, true};
  }
  if (Matches(normalized, {"next track", "skip"})) {
    return RouteResult{Action::MediaNext, normalized, true};
  }
  if (Matches(normalized, {"previous track", "go back"})) {
    return RouteResult{Action::MediaPrevious, normalized, true};
  }
  if (normalized.starts_with("open ") || normalized.starts_with("launch ")) {
    return RouteResult{Action::AppOpen, normalized, true};
  }
  if (normalized.starts_with("close ") || normalized.starts_with("quit ")) {
    return RouteResult{Action::AppClose, normalized, true};
  }
  if (Matches(normalized, {"take a screenshot", "screenshot"})) {
    return RouteResult{Action::Screenshot, normalized, true};
  }
  if (Matches(normalized, {"stop listening"})) {
    return RouteResult{Action::PrivacyModeOn, normalized, false};
  }
  if (Matches(normalized, {"start listening"})) {
    return RouteResult{Action::PrivacyModeOff, normalized, false};
  }
  if (Matches(normalized, {"sleep", "go to sleep"})) {
    return RouteResult{Action::SystemSleep, normalized, true};
  }
  if (Matches(normalized, {"lock", "lock the screen"})) {
    return RouteResult{Action::SystemLock, normalized, true};
  }
  if (Matches(normalized, {"stop"})) {
    return RouteResult{Action::Stop, normalized, false};
  }
  return RouteResult{Action::GeneralQuery, normalized, false};
}

std::expected<void, OkError> CommandRouter::ResetConversation() { return {}; }

} // namespace okcomputer
