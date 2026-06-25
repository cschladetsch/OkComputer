#pragma once

#include "OkComputer/Interfaces.hpp"

#include <vector>

namespace okcomputer {

class StateMachine final : public IStateMachine {
public:
  std::expected<void, OkError> Transition(State state) override;
  std::expected<void, OkError> Stop() override;
  State CurrentState() const override;
  void AddStopHandler(StopHandler handler);

private:
  State state_{State::Idle};
  std::vector<StopHandler> stop_handlers_;
};

} // namespace okcomputer
