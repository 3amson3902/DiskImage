#pragma once
#include <string>
#include <vector>

// Disk imaging options
struct ImagingOptions {
    std::string format = "raw"; // raw, vhd, vmdk, qcow2
    bool compress = false;
    bool sparse = false;
    bool show_progress = true;
    size_t buffer_size = 64 * 1024 * 1024; // 64MB
};

// Main imaging function
bool image_disk(const std::string& src_disk, const std::string& out_file, const ImagingOptions& opts);

// Format conversion (raw <-> vhd/vmdk/qcow2)
bool convert_image(const std::string& src_file, const std::string& out_file, const std::string& format, bool compress);

// Gzip compression for raw images
bool gzip_compress(const std::string& in_file, const std::string& out_file);

// Utility: check if a buffer is all zero
bool is_zero_block(const std::vector<char>& buf);
