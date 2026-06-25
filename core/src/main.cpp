#include "Config.hpp"

#include <iostream>

int main() {
  okcomputer::Config config("okcomputer.config.json");
  const auto loaded = config.Load();
  if (!loaded) {
    std::cerr << loaded.error().code << ": " << loaded.error().message << '\n';
    return 1;
  }
  std::cout << "OkComputer core ready\n";
  return 0;
}
