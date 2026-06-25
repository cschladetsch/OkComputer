cmake_minimum_required(VERSION 3.28)
project(OkComputerCore LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
  add_compile_options(/W4 /WX /EHsc)
else()
  add_compile_options(-Wall -Wextra -Werror)
endif()

add_library(okcomputer_core
  src/AudioCapture.cpp
  src/CommandRouter.cpp
  src/Config.cpp
  src/IPCServer.cpp
  src/KeywordDetector.cpp
  src/StateMachine.cpp
  src/TTSEngine.cpp
)

target_include_directories(okcomputer_core PUBLIC include src)

add_executable(okcomputer_app src/main.cpp)
target_link_libraries(okcomputer_app PRIVATE okcomputer_core)

enable_testing()
add_executable(okcomputer_core_tests
  ../tests/unit/core/test_core.cpp
)
target_link_libraries(okcomputer_core_tests PRIVATE okcomputer_core)
add_test(NAME okcomputer_core_tests COMMAND okcomputer_core_tests)
set_tests_properties(okcomputer_core_tests PROPERTIES WORKING_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}/..")
