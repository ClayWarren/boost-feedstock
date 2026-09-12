:: Test boost::iostreams zlib filter support
@echo on

cd test

cl.exe /EHsc /MD /DBOOST_ALL_DYN_LINK /DBOOST_ZLIB_BINARY=kernel32 /I%PREFIX%\Library\include test_iostreams_zlib.cpp /link /libpath:%PREFIX%\Library\lib
if %ERRORLEVEL% neq 0 exit 1

test_iostreams_zlib.exe
if %ERRORLEVEL% neq 0 exit 1

if "%target_platform%" == "win-arm64" (
    cl.exe /EHsc /MD /std:c++20 /DBOOST_ALL_DYN_LINK /I%LIBRARY_INC% test_context_coroutine.cpp /link /libpath:%LIBRARY_LIB%
    if errorlevel 1 exit /b 1
    test_context_coroutine.exe
    if errorlevel 1 exit /b 1
    cl.exe /EHsc /MD /std:c++20 /I%LIBRARY_INC% test_hana_large.cpp
    if errorlevel 1 exit /b 1
    test_hana_large.exe
    if errorlevel 1 exit /b 1
    dumpbin /headers test_iostreams_zlib.exe | findstr /I /C:"AA64 machine (ARM64)"
    if errorlevel 1 exit /b 1
    dumpbin /headers "%LIBRARY_BIN%\boost_filesystem.dll" | findstr /I /C:"AA64 machine (ARM64)"
    if errorlevel 1 exit /b 1
)
