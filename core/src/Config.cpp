#include "Config.hpp"

#include <chrono>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>

namespace okcomputer {
namespace {

std::string Trim(std::string value) {
  const auto first = value.find_first_not_of(" \t\r\n\"");
  const auto last = value.find_last_not_of(" \t\r\n\",");
  if (first == std::string::npos || last == std::string::npos || last < first) {
    return {};
  }
  return value.substr(first, last - first + 1);
}

} // namespace

Config::Config(std::filesystem::path path) : path_(std::move(path)) {}

std::expected<void, OkError> Config::Load() {
  auto text = ReadWithRetry();
  if (!text) {
    return std::unexpected(text.error());
  }
  auto parsed = ParseFlatValues(*text);
  if (parsed.find("version") == parsed.end() || parsed.find("wake_word") == parsed.end()) {
    return std::unexpected(OkError{"CONFIG_INVALID", "required config keys are missing"});
  }
  cache_ = std::move(parsed);
  return {};
}

std::expected<void, OkError> Config::Watch() { return {}; }

std::expected<std::string, OkError> Config::Get(std::string_view key) const {
  const auto found = cache_.find(std::string(key));
  if (found == cache_.end()) {
    return std::unexpected(OkError{"CONFIG_KEY_MISSING", "config key is not present"});
  }
  return found->second;
}

std::expected<std::string, OkError> Config::ReadWithRetry() const {
  for (int attempt = 0; attempt < 2; ++attempt) {
    std::ifstream file(path_);
    if (file) {
      std::ostringstream buffer;
      buffer << file.rdbuf();
      return buffer.str();
    }
    if (attempt == 0) {
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
  }
  return std::unexpected(OkError{"CONFIG_READ_FAILED", "unable to read config after one retry"});
}

std::map<std::string, std::string> Config::ParseFlatValues(std::string_view json) {
  std::map<std::string, std::string> values;
  std::string input(json);
  size_t pos = 0;
  while ((pos = input.find('"', pos)) != std::string::npos) {
    const size_t key_end = input.find('"', pos + 1);
    if (key_end == std::string::npos) {
      break;
    }
    const std::string key = input.substr(pos + 1, key_end - pos - 1);
    const size_t colon = input.find(':', key_end);
    if (colon == std::string::npos) {
      break;
    }
    const size_t value_end = input.find_first_of(",\n\r}", colon + 1);
    const std::string raw_value = input.substr(colon + 1, value_end - colon - 1);
    values[key] = Trim(raw_value);
    pos = value_end == std::string::npos ? input.size() : value_end + 1;
  }
  return values;
}

template <>
std::expected<std::string, OkError> Config::get<std::string>(std::string_view key) const {
  return Get(key);
}

template <>
std::expected<int, OkError> Config::get<int>(std::string_view key) const {
  auto value = Get(key);
  if (!value) {
    return std::unexpected(value.error());
  }
  return std::stoi(*value);
}

template <>
std::expected<double, OkError> Config::get<double>(std::string_view key) const {
  auto value = Get(key);
  if (!value) {
    return std::unexpected(value.error());
  }
  return std::stod(*value);
}

} // namespace okcomputer
