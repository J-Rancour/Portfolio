#!/usr/bin/env sh
# Builds native/build/libwxcore.so (Linux) or .dylib (macOS) and runs the C++ tests.
set -e
cd "$(dirname "$0")"
mkdir -p build
ext=so
[ "$(uname)" = Darwin ] && ext=dylib

# -fPIC: position-independent code, required for shared libraries on Linux.
${CXX:-g++} -std=c++17 -O2 -Wall -Wextra -fPIC -shared -DWXCORE_BUILD wxcore.cpp -o "build/libwxcore.$ext"
# -rpath '$ORIGIN': look for libwxcore next to the test binary at runtime.
${CXX:-g++} -std=c++17 -O2 -Wall -Wextra test_wxcore.cpp -Lbuild -lwxcore -Wl,-rpath,'$ORIGIN' -o build/test_wxcore
./build/test_wxcore
