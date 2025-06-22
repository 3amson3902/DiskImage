#include "disk_imager_gui.h"
#include <QApplication>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    DiskImagerGui window;
    window.show();
    return app.exec();
}
