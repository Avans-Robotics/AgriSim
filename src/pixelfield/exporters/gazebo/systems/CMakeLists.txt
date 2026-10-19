cmake_minimum_required(VERSION 3.22)
project(pixelfield_systems LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED COMPONENTS register)

# libPixelfieldPullOut.so, loaded by worlds as <plugin filename="PixelfieldPullOut">.
add_library(PixelfieldPullOut SHARED PullOut.cc)
target_link_libraries(PixelfieldPullOut PRIVATE gz-sim8::gz-sim8 gz-plugin2::register)
