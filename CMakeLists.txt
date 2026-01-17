cmake_minimum_required(VERSION 3.18)
project(options_pricing_engine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_compile_options(-O2 -Wall -Wextra)

# ---------------------------------------------------------------------------
# Auto-detect pybind11 cmake directory from the active Python environment.
# Run: pip install pybind11   if this step fails.
# ---------------------------------------------------------------------------
execute_process(
    COMMAND python3 -m pybind11 --cmakedir
    OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE PYBIND11_CMD_RESULT
)

if(NOT PYBIND11_CMD_RESULT EQUAL 0)
    message(FATAL_ERROR
        "Could not locate pybind11. Install it with:\n"
        "    pip install pybind11\n"
        "Then re-run cmake.")
endif()

message(STATUS "pybind11 cmake dir: ${PYBIND11_CMAKE_DIR}")
list(APPEND CMAKE_PREFIX_PATH "${PYBIND11_CMAKE_DIR}")
set(PYBIND11_FINDPYTHON ON) # use modern FindPython; silences CMP0148 deprecation warning
find_package(pybind11 REQUIRED)

# ---------------------------------------------------------------------------
# Static library: options_core
# Contains all pricing logic; shared by the Python module, tests, and bench.
# ---------------------------------------------------------------------------
add_library(options_core STATIC
    src/black_scholes.cpp
    src/batch_pricer.cpp
)
target_include_directories(options_core PUBLIC src/)

# ---------------------------------------------------------------------------
# Python extension module: options_pricer
# Output goes to python/ so scripts can `import options_pricer` directly.
# ---------------------------------------------------------------------------
pybind11_add_module(options_pricer src/bindings.cpp)
target_link_libraries(options_pricer PRIVATE options_core)

set_target_properties(options_pricer PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/python"
)

# ---------------------------------------------------------------------------
# Test executable
# ---------------------------------------------------------------------------
add_executable(test_pricing tests/test_pricing.cpp)
target_link_libraries(test_pricing PRIVATE options_core)

# ---------------------------------------------------------------------------
# Benchmark executable
# ---------------------------------------------------------------------------
add_executable(bench benchmarks/bench.cpp)
target_link_libraries(bench PRIVATE options_core)
