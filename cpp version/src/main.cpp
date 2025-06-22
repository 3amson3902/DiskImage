#include "disk_imager.h"
#include <iostream>
#include <string>

void print_usage() {
    std::cout << "Usage: disk_imager.exe <source_disk> <output_image> [--format raw|vhd|vmdk|qcow2] [--compress] [--progress] [--sparse] [--buffer MB]\n";
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        print_usage();
        return 1;
    }
    std::string src_disk = argv[1];
    std::string out_file = argv[2];
    ImagingOptions opts;
    for (int i = 3; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--format" && i + 1 < argc) {
            opts.format = argv[++i];
        } else if (arg == "--compress") {
            opts.compress = true;
        } else if (arg == "--progress") {
            opts.show_progress = true;
        } else if (arg == "--sparse") {
            opts.sparse = true;
        } else if (arg == "--buffer" && i + 1 < argc) {
            opts.buffer_size = std::stoull(argv[++i]) * 1024 * 1024;
        }
    }
    if (!image_disk(src_disk, out_file, opts)) {
        std::cerr << "Disk imaging failed. See diskimager_cpp.log for details.\n";
        return 2;
    }
    std::cout << "Disk imaging completed successfully.\n";
    return 0;
}
