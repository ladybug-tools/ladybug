# coding=utf-8
from ladybug.config import folders


def test_config_init():
    """Test the initialization of the config module and basic properties."""
    assert hasattr(folders, 'default_epw_folder')
    assert isinstance(folders.default_epw_folder, str)
