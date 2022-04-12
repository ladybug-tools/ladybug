# coding=utf-8
from ladybug.config import folders


def test_config_init():
    """Test the initialization of the config module and basic properties."""
    assert hasattr(folders, 'ladybug_tools_folder')
    assert isinstance(folders.ladybug_tools_folder, str)
    assert hasattr(folders, 'default_epw_folder')
    assert isinstance(folders.default_epw_folder, str)
    assert hasattr(folders, 'python_package_path')
    assert isinstance(folders.python_package_path, str)
    assert hasattr(folders, 'python_exe_path')
    assert isinstance(folders.python_exe_path, str)
