# Cross-platform build: the same file drives MSVC on Windows, GCC/Clang on Linux/macOS.
#   cmake -S native -B native/build -DCMAKE_BUILD_TYPE=Release
#   cmake --build native/build --config Release
#   ctest --test-dir native/build -C Release --output-on-failure
cmake_minimum_required(VERSION 3.16)
project(wxcore LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(wxcore SHARED wxcore.cpp)
target_compile_definitions(wxcore PRIVATE WXCORE_BUILD)
# Put the library directly in build/ (not build/Release/) so Python finds it on
# every platform. The $<1:...> generator expression stops multi-config
# generators like Visual Studio from appending a per-config subfolder.
set_target_properties(wxcore PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "$<1:${CMAKE_BINARY_DIR}>"
    LIBRARY_OUTPUT_DIRECTORY "$<1:${CMAKE_BINARY_DIR}>"
    ARCHIVE_OUTPUT_DIRECTORY "$<1:${CMAKE_BINARY_DIR}>")
if(WIN32)
    set_target_properties(wxcore PROPERTIES PREFIX "")  # wxcore.dll, even with MinGW
endif()

add_executable(test_wxcore test_wxcore.cpp)
target_link_libraries(test_wxcore PRIVATE wxcore)
set_target_properties(test_wxcore PROPERTIES RUNTIME_OUTPUT_DIRECTORY "$<1:${CMAKE_BINARY_DIR}>")

enable_testing()
add_test(NAME wxcore_unit COMMAND test_wxcore)
