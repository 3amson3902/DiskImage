cmake_minimum_required(VERSION 3.15)
project(disk_imager VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)  # Handle Qt moc automatically
set(CMAKE_AUTORCC ON)  # Handle Qt resources
set(CMAKE_AUTOUIC ON)  # Handle Qt UI files

# Set Qt6 path for Windows
set(CMAKE_PREFIX_PATH "C:/Qt/6.9.1/mingw_64")
set(Qt6_DIR "C:/Qt/6.9.1/mingw_64/lib/cmake/Qt6")

option(DISK_IMAGER_GUI "Build with Qt GUI" ON)

# Core source files (always included)
set(CORE_SOURCES
    src/disk_imager.cpp
    src/logger.cpp
    src/progress_bar.cpp
    src/disk_imager_backend.cpp
    src/disk_imager_backend_win.cpp
)

if(DISK_IMAGER_GUI)
    find_package(Qt6 COMPONENTS Widgets REQUIRED)
    
    # Explicitly handle MOC for our GUI class
    qt_wrap_cpp(MOC_FILES include/d
        ${MOC_FILES}
        ${CORE_SOURCES}
    )
    target_link_libraries(disk_imager PRIVATE Qt6::Widgets)
else()
    add_executable(disk_imager
        src/main.cpp
        ${CORE_SOURCES}
    )
endif()

target_include_directories(disk_imager PRIVATE include)

if(WIN32)
    target_link_libraries(disk_imager PRIVATE ws2_32)
endif()
