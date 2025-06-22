#include "disk_imager.h"
#include "logger.h"
#include "progress_bar.h"
#include <windows.h>
#include <iostream>
#include <vector>
#include <string>
#include <filesystem>
#include <cstdio>

bool is_zero_block(const std::vector<char>& buf) {
    for (char c : buf) if (c != 0) return false;
    return true;
}

bool gzip_compress(const std::string& in_file, const std::string& out_file) {
    std::string cmd = "gzip -c \"" + in_file + "\" > \"" + out_file + "\"";
    return std::system(cmd.c_str()) == 0;
}

bool convert_image(const std::string& src_file, const std::string& out_file, const std::string& format, bool compress) {
    std::string qemu = "qemu-img.exe";
    std::string cmd = qemu + " convert -f raw -O " + format;
    if (compress && (format == "qcow2" || format == "vmdk")) cmd += " -c";
    cmd += " \"" + src_file + "\" \"" + out_file + "\"";
    return std::system(cmd.c_str()) == 0;
}

bool image_disk(const std::string& src_disk, const std::string& out_file, const ImagingOptions& opts) {
    Logger logger("diskimager_cpp.log");
    logger.log("Starting disk imaging: " + src_disk + " -> " + out_file);
    HANDLE hDisk = CreateFileA(src_disk.c_str(), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING, 0, nullptr);
    if (hDisk == INVALID_HANDLE_VALUE) {
        logger.log("Failed to open disk: " + src_disk);
        return false;
    }
    std::string raw_path = out_file;
    if (opts.format != "raw") raw_path = out_file + ".tmp.raw";
    HANDLE hOut = CreateFileA(raw_path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hOut == INVALID_HANDLE_VALUE) {
        logger.log("Failed to create output file: " + raw_path);
        CloseHandle(hDisk);
        return false;
    }
    std::vector<char> buffer(opts.buffer_size);
    LARGE_INTEGER totalSize = {0};
    if (!GetFileSizeEx(hDisk, &totalSize)) totalSize.QuadPart = 0;
    size_t totalRead = 0;
    ProgressBar bar(totalSize.QuadPart, 50);
    DWORD bytesRead = 0, bytesWritten = 0;
    while (ReadFile(hDisk, buffer.data(), (DWORD)opts.buffer_size, &bytesRead, nullptr) && bytesRead > 0) {
        if (opts.sparse && is_zero_block(buffer)) {
            LARGE_INTEGER move; move.QuadPart = bytesRead;
            SetFilePointerEx(hOut, move, nullptr, FILE_CURRENT);
        } else {
            WriteFile(hOut, buffer.data(), bytesRead, &bytesWritten, nullptr);
        }
        totalRead += bytesRead;
        if (opts.show_progress && totalSize.QuadPart > 0) bar.update(totalRead);
    }
    if (opts.show_progress) bar.finish();
    CloseHandle(hDisk);
    CloseHandle(hOut);
    logger.log("Disk imaging complete.");
    // Format conversion
    if (opts.format != "raw") {
        if (!convert_image(raw_path, out_file, opts.format, opts.compress)) {
            logger.log("Format conversion failed.");
            std::filesystem::remove(raw_path);
            return false;
        }
        std::filesystem::remove(raw_path);
    } else if (opts.compress) {
        std::string gz_path = out_file + ".gz";
        if (!gzip_compress(out_file, gz_path)) {
            logger.log("Gzip compression failed.");
            return false;
        }
        std::filesystem::remove(out_file);
        std::filesystem::rename(gz_path, out_file);
    }
    logger.log("All operations complete.");
    return true;
}
