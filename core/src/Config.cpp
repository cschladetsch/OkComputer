#include "Config.hpp"

#include <chrono>
#include <cctype>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

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

void SkipWhitespace(const std::string& input, size_t& pos) {
  while (pos < input.size() && std::isspace(static_cast<unsigned char>(input[pos])) != 0) {
    ++pos;
  }
}

std::string ParseString(const std::string& input, size_t& pos) {
  std::string out;
  if (pos >= input.size() || input[pos] != '"') {
    return out;
  }
  ++pos;
  while (pos < input.size()) {
    const char ch = input[pos++];
    if (ch == '\\' && pos < input.size()) {
      out.push_back(input[pos++]);
      continue;
    }
    if (ch == '"') {
      break;
    }
    out.push_back(ch);
  }
  return out;
}

std::string JoinPath(const std::vector<std::string>& path, std::string_view key) {
  std::string joined;
  for (const auto& part : path) {
    if (!joined.empty()) {
      joined.push_back('.');
    }
    joined += part;
  }
  if (!joined.empty()) {
    joined.push_back('.');
  }
  joined += key;
  return joined;
}

void SkipComposite(const std::string& input, size_t& pos, char open, char close) {
  int depth = 1;
  ++pos;
  while (pos < input.size() && depth > 0) {
    if (input[pos] == '"') {
      (void)ParseString(input, pos);
      continue;
    }
    if (input[pos] == open) {
      ++depth;
    } else if (input[pos] == close) {
      --depth;
    }
    ++pos;
  }
}

void ParseObject(const std::string& input, size_t& pos, std::vector<std::string>& path,
                 std::map<std::string, std::string>& values) {
  if (pos >= input.size() || input[pos] != '{') {
    return;
  }
  ++pos;
  while (pos < input.size()) {
    SkipWhitespace(input, pos);
    if (pos >= input.size() || input[pos] == '}') {
      ++pos;
      return;
    }
    if (input[pos] != '"') {
      ++pos;
      continue;
    }
    const std::string key = ParseString(input, pos);
    SkipWhitespace(input, pos);
    if (pos >= input.size() || input[pos] != ':') {
      continue;
    }
    ++pos;
    SkipWhitespace(input, pos);
    if (pos >= input.size()) {
      break;
    }
    if (input[pos] == '{') {
      path.push_back(key);
      ParseObject(input, pos, path, values);
      path.pop_back();
    } else if (input[pos] == '[') {
      SkipComposite(input, pos, '[', ']');
    } else if (input[pos] == '"') {
      values[JoinPath(path, key)] = ParseString(input, pos);
    } else {
      const size_t start = pos;
      while (pos < input.size() && input[pos] != ',' && input[pos] != '}' && input[pos] != ']') {
        ++pos;
      }
      values[JoinPath(path, key)] = Trim(input.substr(start, pos - start));
    }
    SkipWhitespace(input, pos);
    if (pos < input.size() && input[pos] == ',') {
      ++pos;
    }
  }
}

} // namespace

Config::Config(std::filesystem::path path) : path_(std::move(path)) {}

std::expected<void, OkError> Config::Load() {
  auto text = ReadWithRetry();
  if (!text) {
    return std::unexpected(text.error());
  }
  if (!HasBalancedJsonDelimiters(*text)) {
    return std::unexpected(OkError{"CONFIG_INVALID", "config JSON is malformed"});
  }
  auto parsed = ParseFlatValues(*text);
  if (parsed.empty()) {
    return std::unexpected(OkError{"CONFIG_INVALID", "config root did not contain parseable values"});
  }
  ApplyDefaults(parsed);
  cache_ = std::move(parsed);
  if (std::filesystem::exists(path_)) {
    last_write_time_ = std::filesystem::last_write_time(path_);
  }
  return {};
}

std::expected<void, OkError> Config::Watch() {
  if (!std::filesystem::exists(path_)) {
    return std::unexpected(OkError{"CONFIG_READ_FAILED", "config file is missing"});
  }
  const auto write_time = std::filesystem::last_write_time(path_);
  if (last_write_time_.has_value() && *last_write_time_ == write_time) {
    return {};
  }
  auto result = Load();
  if (!result) {
    return std::unexpected(result.error());
  }
  return {};
}

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
  SkipWhitespace(input, pos);
  std::vector<std::string> path;
  ParseObject(input, pos, path, values);
  return values;
}

void Config::ApplyDefaults(std::map<std::string, std::string>& values) {
  const std::map<std::string, std::string> defaults{
      {"version", "1"},
      {"wake_word", "ok computer"},
      {"wake_word_sensitivity", "0.5"},
      {"audio.sample_rate", "16000"},
      {"audio.channels", "1"},
      {"audio.chunk_ms", "30"},
      {"ipc.pipe_name", "okcomputer"},
      {"ipc.ws_port", "5003"},
  };
  for (const auto& [key, value] : defaults) {
    if (!values.contains(key)) {
      values[key] = value;
    }
  }
}

bool Config::HasBalancedJsonDelimiters(std::string_view json) {
  std::vector<char> stack;
  bool in_string = false;
  bool escaped = false;
  for (const char ch : json) {
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch == '\\' && in_string) {
      escaped = true;
      continue;
    }
    if (ch == '"') {
      in_string = !in_string;
      continue;
    }
    if (in_string) {
      continue;
    }
    if (ch == '{' || ch == '[') {
      stack.push_back(ch);
    } else if (ch == '}' || ch == ']') {
      if (stack.empty()) {
        return false;
      }
      const char open = stack.back();
      if ((ch == '}' && open != '{') || (ch == ']' && open != '[')) {
        return false;
      }
      stack.pop_back();
    }
  }
  return !in_string && stack.empty();
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
