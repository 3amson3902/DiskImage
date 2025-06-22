#include "progress_bar.h"
#include <iostream>

ProgressBar::ProgressBar(size_t total, size_t width)
    : total_(total), width_(width) {}

void ProgressBar::update(size_t current) {
    size_t percent = (current * 100) / total_;
    if (percent != last_percent_) {
        size_t pos = (current * width_) / total_;
        std::cout << "[";
        for (size_t i = 0; i < width_; ++i) {
            if (i < pos) std::cout << "=";
            else if (i == pos) std::cout << ">";
            else std::cout << " ";
        }
        std::cout << "] " << percent << "%\r";
        std::cout.flush();
        last_percent_ = percent;
    }
}

void ProgressBar::finish() {
    std::cout << std::endl;
}
