cmake_minimum_required(VERSION 3.12)
project(filter_examples LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

foreach(example basic_filters kalman_1d kalman_position)
    add_executable(${example} ${example}.cpp)
endforeach()

