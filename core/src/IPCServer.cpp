#include "IPCServer.hpp"

namespace okcomputer {

std::expected<void, OkError> IPCServer::Start() {
  running_ = true;
  return {};
}

std::expected<void, OkError> IPCServer::Stop() {
  running_ = false;
  return {};
}

std::expected<void, OkError> IPCServer::SendJson(std::string_view frame) {
  if (!running_) {
    return std::unexpected(OkError{"IPC_DISCONNECTED", "IPC server is not running"});
  }
  if (!frame.starts_with("{") || !frame.ends_with("}")) {
    return std::unexpected(OkError{"INVALID_JSON", "frame is not a JSON object"});
  }
  sent_.emplace_back(frame);
  return {};
}

const std::vector<std::string>& IPCServer::sent() const { return sent_; }

} // namespace okcomputer
