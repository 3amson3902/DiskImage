#include "disk_imager_backend_win.h"
#include <windows.h>
#include <vector>

DiskImagerBackendWin::DiskImagerBackendWin() {}
DiskImagerBackendWin::~DiskImagerBackendWin() { close_disk(); }

bool DiskImagerBackendWin::open_disk(const std::string& path) {
    close_disk();
    hDisk_ = CreateFileA(path.c_str(), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING, 0, nullptr);
    if (hDisk_ == INVALID_HANDLE_VALUE) { hDisk_ = nullptr; return false; }
    LARGE_INTEGER size;
    if (GetFileSizeEx((HANDLE)hDisk_, &size)) diskSize_ = static_cast<size_t>(size.QuadPart);
    else diskSize_ = 0;
    return true;
}

bool DiskImagerBackendWin::read_block(std::vector<char>& buffer, size_t& bytesRead) {
    if (!hDisk_) return false;
    DWORD br = 0;
    if (!ReadFile((HANDLE)hDisk_, buffer.data(), (DWORD)buffer.size(), &br, nullptr)) return false;
    bytesRead = br;
    return br > 0;
}

void DiskImagerBackendWin::close_disk() {
    if (hDisk_) { CloseHandle((HANDLE)hDisk_); hDisk_ = nullptr; }
}

size_t DiskImagerBackendWin::disk_size() const { return diskSize_; }
