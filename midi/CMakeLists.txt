cmake_minimum_required(VERSION 3.21)

set(CMAKE_EXECUTABLE_SUFFIX ${EXECUTABLE_SUFFIX})

project(midi_controller VERSION 1.0.0 LANGUAGES CXX)

add_executable(${PROJECT_NAME} main.cpp)
