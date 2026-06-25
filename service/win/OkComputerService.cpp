#include <windows.h>

// [WIN32] Minimal Windows Service entry point scaffold. Full child-process
// supervision is implemented by scripts/run.ps1 for the no-admin path.

int main(int argc, char** argv) {
  if (argc > 1) {
    return 0;
  }
  return 0;
}
