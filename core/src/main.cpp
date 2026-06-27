#include "Config.hpp"

#include <atomic>
#include <chrono>
#include <csignal>
#include <iostream>
#include <thread>

namespace {

std::atomic_bool running{true};

void HandleSignal(int) {
  running = false;
}

} // namespace

int main() {
  std::signal(SIGINT, HandleSignal);
  std::signal(SIGTERM, HandleSignal);

  okcomputer::Config config("okcomputer.config.json");
  const auto loaded = config.Load();
  if (!loaded) {
    std::cerr << loaded.error().code << ": " << loaded.error().message << '\n';
    return 1;
  }
  std::cout << "OkComputer core ready\n";
  while (running) {
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
  }
  return 0;
}
