#pragma once

#include "OkComputer/Interfaces.hpp"

#include <string>
#include <vector>

namespace okcomputer {

class IPCServer final : public IIPCServer {
public:
  std::expected<void, OkError> Start() override;
  std::expected<void, OkError> Stop() override;
  std::expected<void, OkError> SendJson(std::string_view frame) override;
  const std::vector<std::string>& sent() const;

private:
  bool running_{false};
  std::vector<std::string> sent_;
};

} // namespace okcomputer
