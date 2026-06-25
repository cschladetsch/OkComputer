#include "StateMachine.hpp"

#include <optional>

namespace okcomputer {

std::expected<void, OkError> StateMachine::Transition(State state) {
  if (state_ == State::Privacy && state != State::Idle && state != State::Privacy) {
    return std::unexpected(OkError{"INVALID_STATE_TRANSITION", "privacy mode may only return to idle"});
  }
  state_ = state;
  return {};
}

std::expected<void, OkError> StateMachine::Stop() {
  std::optional<OkError> first_error;
  for (const auto& handler : stop_handlers_) {
    auto result = handler();
    if (!result && !first_error.has_value()) {
      first_error = result.error();
    }
  }
  state_ = State::Idle;
  if (first_error.has_value()) {
    return std::unexpected(*first_error);
  }
  return {};
}

State StateMachine::CurrentState() const { return state_; }

void StateMachine::AddStopHandler(StopHandler handler) { stop_handlers_.push_back(std::move(handler)); }

} // namespace okcomputer
