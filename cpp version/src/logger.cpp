#include "logger.h"
#include <iostream>
#include <chrono>
#include <ctime>

Logger::Logger(const std::string& filename) : ofs(filename, std::ios::app) {}

void Logger::log(const std::string& msg) {
    auto now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    ofs << std::ctime(&now) << ": " << msg << std::endl;
}
