#include "disk_imager_gui.h"
#include "disk_imager_backend.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QLabel>
#include <QProgressBar>
#include <QWidget>
#include <QMenuBar>
#include <QStatusBar>
#include <QComboBox>
#include <QLineEdit>
#include <QFileDialog>
#include <QMessageBox>

DiskImagerGui::DiskImagerGui(QWidget* parent)
    : QMainWindow(parent)
    , backend_(create_backend())
{
    setWindowTitle("Disk Imaging Tool");
    setupUi();
    refreshDiskList();
}

// Force out-of-line virtual destructor for vtable generation
DiskImagerGui::~DiskImagerGui() = default;

void DiskImagerGui::setupUi()
{
    auto* centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    
    auto* layout = new QVBoxLayout(centralWidget);
    
    // Disk selection
    auto* diskLayout = new QHBoxLayout;
    auto* diskLabel = new QLabel("Select Disk:", this);
    diskCombo_ = new QComboBox(this);
    diskLayout->addWidget(diskLabel);
    diskLayout->addWidget(diskCombo_);
    layout->addLayout(diskLayout);
    
    // Output file selection
    auto* fileLayout = new QHBoxLayout;
    auto* fileLabel = new QLabel("Output File:", this);
    outputPath_ = new QLineEdit(this);
    browseButton_ = new QPushButton("Browse", this);
    fileLayout->addWidget(fileLabel);
    fileLayout->addWidget(outputPath_);
    fileLayout->addWidget(browseButton_);
    layout->addLayout(fileLayout);
    
    statusLabel_ = new QLabel("Select a disk and output file to begin", this);
    layout->addWidget(statusLabel_);
    
    progressBar_ = new QProgressBar(this);
    progressBar_->setVisible(false);
    layout->addWidget(progressBar_);
    
    startButton_ = new QPushButton("Start Imaging", this);
    startButton_->setEnabled(false);
    layout->addWidget(startButton_);
    
    connect(startButton_, &QPushButton::clicked, this, &DiskImagerGui::onStartImaging);
    connect(browseButton_, &QPushButton::clicked, this, &DiskImagerGui::onBrowseFile);
    connect(diskCombo_, &QComboBox::currentIndexChanged, this, [this](int index) {
        selectedDisk_ = diskCombo_->itemData(index).toString();
        startButton_->setEnabled(!selectedDisk_.isEmpty() && !outputPath_->text().isEmpty());
    });
    connect(outputPath_, &QLineEdit::textChanged, this, [this]() {
        startButton_->setEnabled(!selectedDisk_.isEmpty() && !outputPath_->text().isEmpty());
    });
    
    setMinimumSize(600, 200);
}

void DiskImagerGui::refreshDiskList()
{
    diskCombo_->clear();
    // TODO: Get disk list from backend
    // For now, add some dummy items
    diskCombo_->addItem("C: System (256GB)", "\\\\?\\PhysicalDrive0");
    diskCombo_->addItem("D: Data (512GB)", "\\\\?\\PhysicalDrive1");
}

void DiskImagerGui::onBrowseFile()
{
    QString fileName = QFileDialog::getSaveFileName(this,
        tr("Save Disk Image"), "",
        tr("Disk Images (*.img);;All Files (*)"));
        
    if (!fileName.isEmpty()) {
        outputPath_->setText(fileName);
    }
}

void DiskImagerGui::onStartImaging()
{
    if (selectedDisk_.isEmpty() || outputPath_->text().isEmpty()) {
        QMessageBox::warning(this, tr("Error"),
                           tr("Please select both a disk and output file"));
        return;
    }
    
    statusLabel_->setText("Imaging in progress...");
    progressBar_->setVisible(true);
    progressBar_->setValue(0);
    startButton_->setEnabled(false);
    diskCombo_->setEnabled(false);
    outputPath_->setEnabled(false);
    browseButton_->setEnabled(false);
    
    // TODO: Start the imaging process using the backend
    // For now, simulate progress
    QTimer::singleShot(1000, this, [this]() {
        progressBar_->setValue(100);
        statusLabel_->setText("Imaging completed successfully");
        diskCombo_->setEnabled(true);
        outputPath_->setEnabled(true);
        browseButton_->setEnabled(true);
        startButton_->setEnabled(true);
    });
}
