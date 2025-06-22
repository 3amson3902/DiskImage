#include "disk_imager_backend.h"
#include "disk_imager_backend_win.h"
#include <memory>

std::unique_ptr<DiskImagerBackend> create_backend() {
    return std::make_unique<DiskImagerBackendWin>();
}
