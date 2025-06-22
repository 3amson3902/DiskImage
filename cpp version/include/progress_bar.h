#pragma once
#include <string>

class ProgressBar {
public:
    ProgressBar(size_t total, size_t width = 50);
    void update(size_t current);
    void finish();
private:
    size_t total_;
    size_t width_;
    size_t last_percent_ = 0;
};
