#pragma once

#include "OkComputer/Interfaces.hpp"

namespace okcomputer {

class CommandRouter final : public ICommandRouter {
public:
  std::expected<RouteResult, OkError> Route(std::string_view text) override;
  std::expected<void, OkError> ResetConversation() override;
};

} // namespace okcomputer
