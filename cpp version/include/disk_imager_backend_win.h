#pragma once
#include <string>
#include <vector>
#include "disk_imager_backend.h"

class DiskImagerBackendWin : public DiskImagerBackend {
public:
    DiskImagerBackendWin();
    ~DiskImagerBackendWin();
    bool open_disk(const std::string& path) override;
    bool read_block(std::vector<char>& buffer, size_t& bytesRead) override;
    void close_disk() override;
    size_t disk_size() const override;
private:
    void* hDisk_ = nullptr;
    size_t diskSize_ = 0;
};
