#pragma once

#include <QMainWindow>
#include <memory>

class QLabel;
class QPushButton;
class QProgressBar;
class QComboBox;
class QLineEdit;
class DiskImagerBackend;

class DiskImagerGui : public QMainWindow {
    Q_OBJECT

public:
    explicit DiskImagerGui(QWidget* parent = nullptr);
    ~DiskImagerGui() override;

private slots:
    void onStartImaging();
    void onBrowseFile();
    void refreshDiskList();

private:
    void setupUi();
    void setupDiskList();

    std::unique_ptr<DiskImagerBackend> backend_;
    QLabel* statusLabel_ = nullptr;
    QPushButton* startButton_ = nullptr;
    QProgressBar* progressBar_ = nullptr;
    QComboBox* diskCombo_ = nullptr;
    QLineEdit* outputPath_ = nullptr;
    QPushButton* browseButton_ = nullptr;
    QString selectedDisk_;
};
