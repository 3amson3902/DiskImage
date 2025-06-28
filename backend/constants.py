"""
Constants and configuration values for DiskImage application.
"""
from pathlib import Path
from typing import List

# File sizes
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024
DEFAULT_BUFFER_SIZE = 64 * BYTES_PER_MB

# Windows error codes
WINDOWS_DLL_NOT_FOUND = 3221225781

# Required QEMU files for Windows
REQUIRED_QEMU_FILES: List[str] = [
    # Root files
    'brlapi-0.8.dll', 'COPYING', 'COPYING.LIB', 'libaom.dll', 'libatk-1.0-0.dll', 'libavif-16.dll', 'libbrotlicommon.dll', 'libbrotlidec.dll', 'libbrotlienc.dll', 'libbz2-1.dll', 'libcacard-0.dll', 'libcairo-2.dll', 'libcairo-gobject-2.dll', 'libcapstone.dll', 'libcrypto-3-x64.dll', 'libcurl-4.dll', 'libdatrie-1.dll', 'libdav1d-7.dll', 'libdb-6.0.dll', 'libdeflate.dll', 'libepoxy-0.dll', 'libexpat-1.dll', 'libfdt-1.dll', 'libffi-8.dll', 'libfontconfig-1.dll', 'libfreetype-6.dll', 'libfribidi-0.dll', 'libgcc_s_seh-1.dll', 'libgdk-3-0.dll', 'libgdk_pixbuf-2.0-0.dll', 'libgio-2.0-0.dll', 'libglib-2.0-0.dll', 'libgmodule-2.0-0.dll', 'libgmp-10.dll', 'libgnutls-30.dll', 'libgobject-2.0-0.dll', 'libgraphite2.dll', 'libgstapp-1.0-0.dll', 'libgstbase-1.0-0.dll', 'libgstreamer-1.0-0.dll', 'libgtk-3-0.dll', 'libharfbuzz-0.dll', 'libhogweed-6.dll', 'libhwy.dll', 'libiconv-2.dll', 'libidn2-0.dll', 'libintl-8.dll', 'libjack64.dll', 'libjbig-0.dll', 'libjpeg-8.dll', 'libjxl.dll', 'libjxl_cms.dll', 'liblcms2-2.dll', 'libLerc.dll', 'liblz4.dll', 'liblzma-5.dll', 'liblzo2-2.dll', 'libncursesw6.dll', 'libnettle-8.dll', 'libnfs-14.dll', 'libnspr4.dll', 'libopus-0.dll', 'liborc-0.4-0.dll', 'libp11-kit-0.dll', 'libpango-1.0-0.dll', 'libpangocairo-1.0-0.dll', 'libpangoft2-1.0-0.dll', 'libpangowin32-1.0-0.dll', 'libpcre2-8-0.dll', 'libpixman-1-0.dll', 'libplc4.dll', 'libplds4.dll', 'libpng16-16.dll', 'libpsl-5.dll', 'librav1e.dll', 'libsasl2-3.dll', 'libsharpyuv-0.dll', 'libslirp-0.dll', 'libsnappy.dll', 'libspice-server-1.dll', 'libssh.dll', 'libssh2-1.dll', 'libssl-3-x64.dll', 'libssp-0.dll', 'libstdc++-6.dll', 'libSvtAv1Enc-3.dll', 'libsystre-0.dll', 'libtasn1-6.dll', 'libthai-0.dll', 'libtiff-6.dll', 'libtre-5.dll', 'libunistring-5.dll', 'libusb-1.0.dll', 'libusbredirparser-1.dll', 'libvirglrenderer-1.dll', 'libwebp-7.dll', 'libwebpdemux-2.dll', 'libwinpthread-1.dll', 'libyuv.dll', 'libzstd.dll', 'nss3.dll', 'nssutil3.dll', 'qemu-edid.exe', 'qemu-ga.exe', 'qemu-img.exe', 'qemu-io.exe', 'qemu-nbd.exe', 'qemu-storage-daemon.exe', 'qemu-system-aarch64.exe', 'qemu-system-aarch64w.exe', 'qemu-system-alpha.exe', 'qemu-system-alphaw.exe', 'qemu-system-arm.exe', 'qemu-system-armw.exe', 'qemu-system-avr.exe', 'qemu-system-avrw.exe', 'qemu-system-hppa.exe', 'qemu-system-hppaw.exe', 'qemu-system-i386.exe', 'qemu-system-i386w.exe', 'qemu-system-loongarch64.exe', 'qemu-system-loongarch64w.exe', 'qemu-system-m68k.exe', 'qemu-system-m68kw.exe', 'qemu-system-microblaze.exe', 'qemu-system-microblazeel.exe', 'qemu-system-microblazeelw.exe', 'qemu-system-microblazew.exe', 'qemu-system-mips.exe', 'qemu-system-mips64.exe', 'qemu-system-mips64el.exe', 'qemu-system-mips64elw.exe', 'qemu-system-mips64w.exe', 'qemu-system-mipsel.exe', 'qemu-system-mipselw.exe', 'qemu-system-mipsw.exe', 'qemu-system-or1k.exe', 'qemu-system-or1kw.exe', 'qemu-system-ppc.exe', 'qemu-system-ppc64.exe', 'qemu-system-ppc64w.exe', 'qemu-system-ppcw.exe', 'qemu-system-riscv32.exe', 'qemu-system-riscv32w.exe', 'qemu-system-riscv64.exe', 'qemu-system-riscv64w.exe', 'qemu-system-rx.exe', 'qemu-system-rxw.exe', 'qemu-system-s390x.exe', 'qemu-system-s390xw.exe', 'qemu-system-sh4.exe', 'qemu-system-sh4eb.exe', 'qemu-system-sh4ebw.exe', 'qemu-system-sh4w.exe', 'qemu-system-sparc.exe', 'qemu-system-sparc64.exe', 'qemu-system-sparc64w.exe', 'qemu-system-sparcw.exe', 'qemu-system-tricore.exe', 'qemu-system-tricorew.exe', 'qemu-system-x86_64.exe', 'qemu-system-x86_64w.exe', 'qemu-system-xtensa.exe', 'qemu-system-xtensaeb.exe', 'qemu-system-xtensaebw.exe', 'qemu-system-xtensaw.exe', 'qemu-uninstall.exe', 'README.rst', 'SDL2.dll', 'SDL2_image.dll', 'VERSION', 'zlib1.dll',
    # lib/gdk-pixbuf-2.0/2.10.0/
    'lib/gdk-pixbuf-2.0/2.10.0/loaders.cache',
    # share/
    'share/bamboo.dtb', 'share/bios-256k.bin', 'share/bios-microvm.bin', 'share/bios.bin', 'share/canyonlands.dtb', 'share/edk2-aarch64-code.fd', 'share/edk2-arm-code.fd', 'share/edk2-arm-vars.fd', 'share/edk2-i386-code.fd', 'share/edk2-i386-secure-code.fd', 'share/edk2-i386-vars.fd', 'share/edk2-licenses.txt', 'share/edk2-loongarch64-code.fd', 'share/edk2-loongarch64-vars.fd', 'share/edk2-riscv-code.fd', 'share/edk2-riscv-vars.fd', 'share/edk2-x86_64-code.fd', 'share/edk2-x86_64-secure-code.fd', 'share/efi-e1000.rom', 'share/efi-e1000e.rom', 'share/efi-eepro100.rom', 'share/efi-ne2k_pci.rom', 'share/efi-pcnet.rom', 'share/efi-rtl8139.rom', 'share/efi-virtio.rom', 'share/efi-vmxnet3.rom', 'share/hppa-firmware.img', 'share/hppa-firmware64.img', 'share/kvmvapic.bin', 'share/linuxboot.bin', 'share/linuxboot_dma.bin', 'share/multiboot.bin', 'share/multiboot_dma.bin', 'share/npcm7xx_bootrom.bin', 'share/npcm8xx_bootrom.bin', 'share/openbios-ppc', 'share/openbios-sparc32', 'share/openbios-sparc64', 'share/opensbi-riscv32-generic-fw_dynamic.bin', 'share/opensbi-riscv64-generic-fw_dynamic.bin', 'share/palcode-clipper', 'share/petalogix-ml605.dtb', 'share/petalogix-s3adsp1800.dtb', 'share/pnv-pnor.bin', 'share/pvh.bin', 'share/pxe-e1000.rom', 'share/pxe-eepro100.rom', 'share/pxe-ne2k_pci.rom', 'share/pxe-pcnet.rom', 'share/pxe-rtl8139.rom', 'share/pxe-virtio.rom', 'share/qboot.rom', 'share/QEMU,cgthree.bin', 'share/QEMU,tcx.bin', 'share/qemu-nsis.bmp', 'share/qemu_vga.ndrv', 'share/s390-ccw.img', 'share/skiboot.lid', 'share/slof.bin', 'share/trace-events-all', 'share/u-boot-sam460-20100605.bin', 'share/u-boot.e500', 'share/vgabios-ati.bin', 'share/vgabios-bochs-display.bin', 'share/vgabios-cirrus.bin', 'share/vgabios-qxl.bin', 'share/vgabios-ramfb.bin', 'share/vgabios-stdvga.bin', 'share/vgabios-virtio.bin', 'share/vgabios-vmware.bin', 'share/vgabios.bin', 'share/vof-nvram.bin', 'share/vof.bin',
    # share/applications/
    'share/applications/qemu.desktop',
]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
QEMU_DIR = TOOLS_DIR / "qemu"
SEVENZIP_DIR = TOOLS_DIR / "7zip"
CONFIG_FILE = PROJECT_ROOT / "config.json"
LOG_FILE = PROJECT_ROOT / "diskimager_main.log"

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {
    "Raw (.img)": "img",
    "VHD (.vhd)": "vhd", 
    "VMDK (.vmdk)": "vmdk",
    "QCOW2 (.qcow2)": "qcow2",
    "ISO (.iso)": "iso"
}

# Archive formats
SUPPORTED_ARCHIVE_FORMATS = ["zip", "7z"]

# Sparse image formats (formats that support compression)
SPARSE_FORMATS = {"qcow2", "vhd", "vmdk"}
COMPRESSIBLE_FORMATS = {"qcow2", "vmdk"}

# Default configuration
DEFAULT_CONFIG: dict[str, object] = {
    "cleanup_tools": True,
    "last_output_dir": "",
    "theme": "auto",
    "window_size": [1024, 768],
    "buffer_size_mb": 64
}

# Archive preferences (.zip > .7z > .exe for QEMU)
ARCHIVE_PRIORITY = {'.zip': 0, '.7z': 1, '.exe': 2}

# Third-party software download URLs
# QEMU installer (will be extracted for portable use)
QEMU_WINDOWS_URL = "https://qemu.weilnetz.de/w64/qemu-w64-setup-20250422.exe"
SEVENZIP_WINDOWS_URL = "https://www.7-zip.org/a/7z2301-x64.exe"
