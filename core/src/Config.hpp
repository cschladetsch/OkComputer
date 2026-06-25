#pragma once

#include "OkComputer/Interfaces.hpp"

#include <filesystem>
#include <map>
#include <optional>

namespace okcomputer {

class Config final : public IConfigLoader {
public:
  explicit Config(std::filesystem::path path);
  std::expected<void, OkError> Load() override;
  std::expected<void, OkError> Watch() override;
  std::expected<std::string, OkError> Get(std::string_view key) const override;

  template <typename T>
  std::expected<T, OkError> get(std::string_view key) const;

private:
  std::expected<std::string, OkError> ReadWithRetry() const;
  static std::map<std::string, std::string> ParseFlatValues(std::string_view json);
  static void ApplyDefaults(std::map<std::string, std::string>& values);
  static bool HasBalancedJsonDelimiters(std::string_view json);

  std::filesystem::path path_;
  std::map<std::string, std::string> cache_;
  std::optional<std::filesystem::file_time_type> last_write_time_;
};

template <>
std::expected<std::string, OkError> Config::get<std::string>(std::string_view key) const;

template <>
std::expected<int, OkError> Config::get<int>(std::string_view key) const;

template <>
std::expected<double, OkError> Config::get<double>(std::string_view key) const;

} // namespace okcomputer
