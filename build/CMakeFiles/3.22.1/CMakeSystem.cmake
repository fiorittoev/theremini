set(CMAKE_HOST_SYSTEM "Linux-5.15.167.4-microsoft-standard-WSL2")
set(CMAKE_HOST_SYSTEM_NAME "Linux")
set(CMAKE_HOST_SYSTEM_VERSION "5.15.167.4-microsoft-standard-WSL2")
set(CMAKE_HOST_SYSTEM_PROCESSOR "x86_64")

include("/opt/wasi-sdk/share/cmake/wasi-sdk.cmake")

set(CMAKE_SYSTEM "WASI-1")
set(CMAKE_SYSTEM_NAME "WASI")
set(CMAKE_SYSTEM_VERSION "1")
set(CMAKE_SYSTEM_PROCESSOR "wasm32")

set(CMAKE_CROSSCOMPILING "TRUE")

set(CMAKE_SYSTEM_LOADED 1)
