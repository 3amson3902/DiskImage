"""
Test suite for CLI interface.
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from cli.main import main, list_available_disks, create_disk_image


class TestCLIMain:
    """Test CLI main functionality."""
    
    @patch('cli.main.list_disks')
    def test_list_available_disks_success(self, mock_list_disks, capsys):
        """Test successful disk listing."""
        mock_list_disks.return_value = [
            {
                'id': '\\\\.\\PHYSICALDRIVE0',
                'name': 'System Disk',
                'size': '500GB',
                'type': 'Fixed'
            },
            {
                'id': '\\\\.\\PHYSICALDRIVE1', 
                'name': 'USB Drive',
                'size': '32GB',
                'type': 'Removable'
            }
        ]
        
        list_available_disks()
        captured = capsys.readouterr()
        
        assert "Available disks:" in captured.out
        assert "System Disk" in captured.out
        assert "USB Drive" in captured.out
        assert "\\\\.\\PHYSICALDRIVE0" in captured.out
    
    @patch('cli.main.list_disks')
    def test_list_available_disks_empty(self, mock_list_disks, capsys):
        """Test disk listing when no disks found."""
        mock_list_disks.return_value = []
        
        list_available_disks()
        captured = capsys.readouterr()
        
        assert "No disks found." in captured.out
    
    @patch('cli.main.list_disks')
    def test_list_available_disks_error(self, mock_list_disks):
        """Test disk listing with error."""
        mock_list_disks.side_effect = Exception("Test error")
        
        with pytest.raises(SystemExit):
            list_available_disks()
    
    @patch('sys.argv', ['diskimage', '--list'])
    @patch('cli.main.list_available_disks')
    def test_main_list_action(self, mock_list):
        """Test main function with list action."""
        main()
        mock_list.assert_called_once()
    
    @patch('sys.argv', ['diskimage', '--disk', 'test', '--output', 'test.img'])
    @patch('cli.main.create_disk_image')
    def test_main_create_image(self, mock_create):
        """Test main function with image creation."""
        main()
        mock_create.assert_called_once()
    
    def test_main_missing_disk_argument(self, capsys):
        """Test main function with missing disk argument."""
        with patch('sys.argv', ['diskimage', '--output', 'test.img']):
            with pytest.raises(SystemExit):
                main()


class TestCLIImageCreation:
    """Test CLI image creation functionality."""
    
    @patch('cli.main.is_admin')
    @patch('cli.main.list_disks')
    @patch('cli.main.ImagingWorker')
    @patch('builtins.input')
    def test_create_disk_image_success(self, mock_input, mock_worker, mock_list_disks, mock_is_admin):
        """Test successful disk image creation."""
        # Setup mocks
        mock_is_admin.return_value = True
        mock_list_disks.return_value = [
            {'id': 'test_disk', 'name': 'Test Disk'}
        ]
        
        mock_worker_instance = Mock()
        mock_worker.return_value = mock_worker_instance
        mock_worker_instance.create_image.return_value = (True, "Success")
        
        # Mock user input for overwrite confirmation
        mock_input.return_value = 'n'
        
        with patch('pathlib.Path.exists', return_value=False):
            create_disk_image(
                disk_id='test_disk',
                output_path='test.img',
                verbose=False
            )
        
        mock_worker_instance.create_image.assert_called_once()
    
    @patch('cli.main.is_admin')
    def test_create_disk_image_no_admin(self, mock_is_admin):
        """Test image creation without admin privileges."""
        mock_is_admin.return_value = False
        
        with pytest.raises(SystemExit):
            create_disk_image(
                disk_id='test_disk',
                output_path='test.img'
            )
    
    @patch('cli.main.is_admin')
    @patch('cli.main.list_disks')
    def test_create_disk_image_disk_not_found(self, mock_list_disks, mock_is_admin):
        """Test image creation with non-existent disk."""
        mock_is_admin.return_value = True
        mock_list_disks.return_value = []
        
        with pytest.raises(SystemExit):
            create_disk_image(
                disk_id='nonexistent_disk',
                output_path='test.img'
            )
    
    @patch('cli.main.is_admin')
    @patch('cli.main.list_disks')
    @patch('cli.main.ImagingWorker')
    @patch('builtins.input')
    def test_create_disk_image_overwrite_confirmation(self, mock_input, mock_worker, mock_list_disks, mock_is_admin):
        """Test image creation with overwrite confirmation."""
        mock_is_admin.return_value = True
        mock_list_disks.return_value = [
            {'id': 'test_disk', 'name': 'Test Disk'}
        ]
        
        # User chooses not to overwrite
        mock_input.return_value = 'n'
        
        with patch('pathlib.Path.exists', return_value=True):
            create_disk_image(
                disk_id='test_disk',
                output_path='test.img'
            )
        
        # ImagingWorker should not be called
        mock_worker.assert_not_called()
    
    @patch('cli.main.is_admin')
    @patch('cli.main.list_disks')
    @patch('cli.main.ImagingWorker')
    def test_create_disk_image_failure(self, mock_worker, mock_list_disks, mock_is_admin):
        """Test image creation failure."""
        mock_is_admin.return_value = True
        mock_list_disks.return_value = [
            {'id': 'test_disk', 'name': 'Test Disk'}
        ]
        
        mock_worker_instance = Mock()
        mock_worker.return_value = mock_worker_instance
        mock_worker_instance.create_image.return_value = (False, "Error message")
        
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(SystemExit):
                create_disk_image(
                    disk_id='test_disk',
                    output_path='test.img'
                )


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_help_option(self, capsys):
        """Test --help option."""
        with patch('sys.argv', ['diskimage', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_format_validation(self):
        """Test image format validation."""
        from cli.main import main
        
        with patch('sys.argv', ['diskimage', '--disk', 'test', '--output', 'test.img', '--format', 'invalid']):
            with pytest.raises(SystemExit):
                main()
    
    def test_archive_type_validation(self):
        """Test archive type validation."""
        from cli.main import main
        
        with patch('sys.argv', ['diskimage', '--disk', 'test', '--output', 'test.img', '--archive', '--archive-type', 'invalid']):
            with pytest.raises(SystemExit):
                main()


if __name__ == "__main__":
    pytest.main([__file__])
