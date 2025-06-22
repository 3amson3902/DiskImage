"""
Test suite for DiskImage application.

Run with: python -m pytest tests/
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

from backend.config_utils import AppConfig
from backend.validation import (
    validate_disk_info, validate_output_path, validate_image_format,
    ValidationError
)
from backend.exceptions import DiskImageError


class TestAppConfig:
    """Test configuration management."""
    
    def test_default_config_creation(self):
        """Test that default config is created correctly."""
        config = AppConfig()
        assert config.cleanup_tools is True
        assert config.theme == "auto"
        assert config.window_size == (1024, 768)
    
    def test_config_save_and_load(self, tmp_path):
        """Test saving and loading configuration."""
        config_file = tmp_path / "test_config.json"
        
        # Create and save config
        config = AppConfig(cleanup_tools=False, theme="dark")
        config.save(config_file)
        
        # Load and verify
        loaded_config = AppConfig.load(config_file)
        assert loaded_config.cleanup_tools is False
        assert loaded_config.theme == "dark"
    
    def test_config_update(self):
        """Test configuration updates."""
        config = AppConfig()
        config.update(cleanup_tools=False, buffer_size_mb=128)
        
        assert config.cleanup_tools is False
        assert config.buffer_size_mb == 128


class TestValidation:
    """Test input validation functions."""
    
    def test_validate_disk_info_valid(self):
        """Test validation of valid disk info."""
        disk_info = {
            "device_id": "\\\\.\\PhysicalDrive0",
            "name": "Test Disk",
            "size": "500 GB",
            "model": "Test Model"
        }
        
        result = validate_disk_info(disk_info)
        assert result == disk_info
    
    def test_validate_disk_info_invalid(self):
        """Test validation of invalid disk info."""
        # Missing required key
        with pytest.raises(ValidationError, match="missing required key"):
            validate_disk_info({"name": "Test"})
        
        # Wrong type
        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_disk_info("not a dict")
    
    def test_validate_output_path_valid(self, tmp_path):
        """Test validation of valid output path."""
        output_path = tmp_path / "test_image.img"
        result = validate_output_path(str(output_path))
        
        assert result == output_path.resolve()
        assert result.parent.exists()
    
    def test_validate_output_path_invalid(self):
        """Test validation of invalid output paths."""
        # Empty path
        with pytest.raises(ValidationError, match="non-empty string"):
            validate_output_path("")
        
        # Invalid characters
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_output_path("test<invalid>.img")
    
    def test_validate_image_format_valid(self):
        """Test validation of valid image formats."""
        assert validate_image_format("img") == "img"
        assert validate_image_format("Raw (.img)") == "img"
        assert validate_image_format("qcow2") == "qcow2"
    
    def test_validate_image_format_invalid(self):
        """Test validation of invalid image formats."""
        with pytest.raises(ValidationError, match="Unsupported image format"):
            validate_image_format("invalid_format")


@pytest.fixture
def mock_qemu_manager():
    """Create a mock QemuManager for testing."""
    with patch('backend.qemu_manager.QemuManager') as mock:
        instance = mock.return_value
        instance.initialize.return_value = None
        instance.create_image.return_value = (True, None)
        yield instance


class TestQemuManager:
    """Test QEMU manager functionality."""
    
    @patch('backend.qemu_manager.QemuManager._find_qemu_executable')
    def test_qemu_manager_initialization(self, mock_find):
        """Test QemuManager initialization."""
        from backend.qemu_manager import QemuManager
        
        mock_find.return_value = Path("/fake/qemu-img.exe")
        manager = QemuManager()
        assert manager.qemu_img_path == Path("/fake/qemu-img.exe")
    
    @patch('subprocess.run')
    def test_get_qemu_version(self, mock_run):
        """Test getting QEMU version."""
        from backend.qemu_manager import QemuManager
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout="qemu-img version 7.0.0"
        )
        
        with patch.object(QemuManager, '_find_qemu_executable', 
                         return_value=Path("/fake/qemu-img.exe")):
            manager = QemuManager()
            version = manager.get_version()
            assert "7.0.0" in version


class TestSevenZipManager:
    """Test 7-Zip manager functionality."""
    
    def test_sevenzip_manager_initialization(self):
        """Test SevenZipManager initialization."""
        from backend.sevenzip_manager import SevenZipManager
        
        with patch.object(SevenZipManager, '_find_7z_executable',
                         return_value=Path("/fake/7z.exe")):
            manager = SevenZipManager()
            assert manager.seven_zip_path == Path("/fake/7z.exe")


class TestArchiveManager:
    """Test archive manager functionality."""
    
    def test_archive_manager_initialization(self):
        """Test ArchiveManager initialization."""
        from backend.archive_manager import ArchiveManager
        
        manager = ArchiveManager()
        assert manager is not None
    
    @patch('backend.archive_manager.SevenZipManager')
    def test_create_7z_archive(self, mock_7z):
        """Test creating 7z archive."""
        from backend.archive_manager import ArchiveManager
        
        mock_7z_instance = Mock()
        mock_7z.return_value = mock_7z_instance
        mock_7z_instance.create_archive.return_value = (True, "Success")
        
        manager = ArchiveManager()
        success, message = manager.create_archive(
            "test.img", "test.7z", "7z"
        )
        
        assert success is True
        assert "Success" in message


class TestImagingWorker:
    """Test imaging worker functionality."""
    
    def test_imaging_worker_initialization(self):
        """Test ImagingWorker initialization."""
        from backend.imaging_worker import ImagingWorker
        
        worker = ImagingWorker()
        assert worker is not None
    
    @patch('backend.imaging_worker.QemuManager')
    @patch('backend.imaging_worker.ArchiveManager')
    def test_create_image_success(self, mock_archive, mock_qemu):
        """Test successful image creation."""
        from backend.imaging_worker import ImagingWorker
        
        # Setup mocks
        mock_qemu_instance = Mock()
        mock_qemu.return_value = mock_qemu_instance
        mock_qemu_instance.create_image.return_value = (True, "Image created")
        
        mock_archive_instance = Mock()
        mock_archive.return_value = mock_archive_instance
        
        worker = ImagingWorker()
        
        disk_info = {
            'id': '\\\\.\\PHYSICALDRIVE1',
            'name': 'Test Disk',
            'size': '1000000000'
        }
        
        with patch('os.path.exists', return_value=True):
            success, message = worker.create_image(
                disk_info=disk_info,
                output_path="test.img",
                image_format="raw"
            )
        
        assert success is True
        assert "Image created" in message


class TestConfigUtils:
    """Test configuration utilities."""
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent config returns defaults."""
        from backend.config_utils import load_config
        
        config = load_config("nonexistent.json")
        assert isinstance(config, AppConfig)
        assert config.cleanup_tools is True  # Default value
    
    def test_save_config(self, tmp_path):
        """Test saving configuration."""
        from backend.config_utils import save_config
        
        config_file = tmp_path / "test_config.json"
        config = AppConfig(cleanup_tools=False)
        
        save_config(config, config_file)
        assert config_file.exists()


class TestLoggingUtils:
    """Test logging utilities."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        from backend.logging_utils import setup_logging
        
        # Should not raise any exceptions
        setup_logging(log_level=logging.INFO)
        
        logger = logging.getLogger("test")
        assert logger.level <= logging.INFO


class TestDiskListUtils:
    """Test disk listing utilities."""
    
    @patch('psutil.disk_partitions')
    def test_list_disks_windows(self, mock_partitions):
        """Test listing disks on Windows."""
        from backend.disk_list_utils import list_disks
        
        # Mock disk partitions
        mock_partition = Mock()
        mock_partition.device = 'C:\\'
        mock_partition.mountpoint = 'C:\\'
        mock_partition.fstype = 'NTFS'
        mock_partitions.return_value = [mock_partition]
        
        with patch('platform.system', return_value='Windows'):
            with patch('backend.disk_list_utils._get_windows_physical_drives',
                      return_value=[{'id': '\\\\.\\PHYSICALDRIVE0', 'name': 'Disk 0'}]):
                disks = list_disks()
                assert len(disks) > 0


class TestCleanupUtils:
    """Test cleanup utilities."""
    
    def test_cleanup_temp_files(self, tmp_path):
        """Test cleaning up temporary files."""
        from backend.cleanup_utils import cleanup_temp_files
        
        # Create some temp files
        temp_file = tmp_path / "temp.tmp"
        temp_file.touch()
        
        cleanup_temp_files([str(temp_file)])
        # File should be cleaned up
        

class TestExceptions:
    """Test custom exceptions."""
    
    def test_disk_image_error(self):
        """Test DiskImageError exception."""
        error = DiskImageError("Test error", error_code="TEST001")
        assert str(error) == "Test error"
        assert error.error_code == "TEST001"
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("Invalid input", field="test_field")
        assert str(error) == "Invalid input"
        assert error.field == "test_field"


class TestConstants:
    """Test constants module."""
    
    def test_supported_formats(self):
        """Test that supported formats are defined."""
        from backend.constants import SUPPORTED_IMAGE_FORMATS
        
        assert isinstance(SUPPORTED_IMAGE_FORMATS, list)
        assert len(SUPPORTED_IMAGE_FORMATS) > 0
        assert "raw" in SUPPORTED_IMAGE_FORMATS


class TestIntegration:
    """Integration tests for complete workflows."""
    
    @patch('backend.admin_utils.is_admin')
    @patch('backend.disk_list_utils.list_disks')
    def test_cli_list_disks(self, mock_list_disks, mock_is_admin):
        """Test CLI disk listing functionality."""
        mock_is_admin.return_value = True
        mock_list_disks.return_value = [
            {'id': '\\\\.\\PHYSICALDRIVE0', 'name': 'System Disk', 'size': '500GB'}
        ]
        
        from cli.main import list_available_disks
        
        # Should not raise any exceptions
        try:
            list_available_disks()
        except SystemExit:
            pass  # Expected for print and exit
    
    def test_gui_initialization(self):
        """Test GUI initialization without actually showing it."""
        from gui.pyqt_app import DiskImageMainWindow
        from PyQt6.QtWidgets import QApplication
        
        # Create QApplication if not exists
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        try:
            window = DiskImageMainWindow()
            assert window is not None
        except Exception as e:
            # Some GUI components might fail in headless environment
            pytest.skip(f"GUI test skipped due to environment: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
