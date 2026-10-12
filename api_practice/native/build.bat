@echo off
rem Builds native\build\wxcore.dll with MSVC and runs the C++ tests.
rem The DLL must match Python's bitness: 64-bit Python needs a 64-bit DLL,
rem which is why this calls vcvars64 (and why 32-bit MinGW won't work).
setlocal
cd /d "%~dp0"

where cl >nul 2>nul && goto build
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
for /f "usebackq delims=" %%i in (`"%VSWHERE%" -latest -products * -find VC\Auxiliary\Build\vcvars64.bat`) do set "VCVARS=%%i"
if not defined VCVARS (
    echo MSVC not found. Install Visual Studio Build Tools with the C++ workload.
    exit /b 1
)
call "%VCVARS%" >nul 2>nul

:build
if not exist build mkdir build
cl /nologo /std:c++17 /O2 /EHsc /W4 /LD /DWXCORE_BUILD wxcore.cpp /Fobuild\ /Febuild\wxcore.dll || exit /b 1
cl /nologo /std:c++17 /O2 /EHsc /W4 test_wxcore.cpp build\wxcore.lib /Fobuild\ /Febuild\test_wxcore.exe || exit /b 1
rem The test exe finds wxcore.dll because Windows searches the exe's own folder first.
build\test_wxcore.exe
