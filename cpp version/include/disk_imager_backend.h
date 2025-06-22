#pragma once
#include <string>
#include <memory>
#include <vector> // Add this include for std::vector

class DiskImagerBackend {
public:
    virtual ~DiskImagerBackend() = default;
    virtual bool open_disk(const std::string& path) = 0;
    virtual bool read_block(std::vector<char>& buffer, size_t& bytesRead) = 0;
    virtual void close_disk() = 0;
    virtual size_t disk_size() const = 0;
};

std::unique_ptr<DiskImagerBackend> create_backend();
