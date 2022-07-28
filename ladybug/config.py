"""Ladybug configurations.

Import this into every module where access configurations are needed.

Usage:
    from ladybug.config import folders
    print(folders.default_epw_folder)
    folders.default_epw_folder = "C:/epw_data"
"""
import os
import platform
import sys
import subprocess
import json


class Folders(object):
    """Ladybug folders.

    Args:
        config_file: The path to the config.json file from which folders are loaded.
            If None, the config.json module included in this package will be used.
            Default: None.
        mute: If False, the paths to the various folders will be printed as they
            are found. If True, no printing will occur upon initialization of this
            class. Default: True.

    Properties:
        * ladybug_tools_folder
        * default_epw_folder
        * python_package_path
        * python_scripts_path
        * python_exe_path
        * python_version
        * python_version_str
        * config_file
        * mute
    """

    def __init__(self, config_file=None, mute=True):
        # set the mute value
        self.mute = bool(mute)

        # load paths from the config JSON file
        self.config_file = config_file

        # set python version to only be retrieved if requested
        self._python_version = None
        self._python_version_str = None

    @property
    def ladybug_tools_folder(self):
        """Get or set the path to the ladybug tools installation folder."""
        return self._ladybug_tools_folder

    @ladybug_tools_folder.setter
    def ladybug_tools_folder(self, path):
        if not path:  # check the default location for epw files
            path = self._find_default_ladybug_tools_folder()

        self._ladybug_tools_folder = path

        if not self.mute and self._ladybug_tools_folder:
            print('Path to the ladybug tools installation folder is set to: '
                  '{}'.format(self._ladybug_tools_folder))

    @property
    def default_epw_folder(self):
        """Get or set the path to the default folder where EPW files are stored."""
        return self._default_epw_folder

    @default_epw_folder.setter
    def default_epw_folder(self, path):
        if not path:  # check the default location for epw files
            path = self._find_default_epw_folder()

        self._default_epw_folder = path

        if not self.mute and self._default_epw_folder:
            print('Path to the default epw folder is set to: '
                  '{}'.format(self._default_epw_folder))

    @property
    def python_package_path(self):
        """Get the path to where this Python package is installed."""
        # check the ladybug_tools folder for a Python installation
        py_pack = None
        lb_install = self.ladybug_tools_folder
        if os.path.isdir(lb_install):
            if os.name == 'nt':
                py_pack = os.path.join(lb_install, 'python', 'Lib', 'site-packages')
            elif platform.system() == 'Darwin':  # on mac, python version is in path
                py_pack = os.path.join(
                    lb_install, 'python', 'lib', 'python3.7', 'site-packages')
        if py_pack is not None and os.path.isdir(py_pack):
            return py_pack
        return os.path.split(os.path.dirname(__file__))[0]  # we're on some other cPython

    @property
    def python_scripts_path(self):
        """Get the path to where Python CLI executable files are installed.

        This can be used to call command line interface (CLI) executable files
        directly (instead of using their usual entry points).
        """
        # check the ladybug_tools folder for a Python installation
        lb_install = self.ladybug_tools_folder
        if os.path.isdir(lb_install):
            py_scripts = os.path.join(lb_install, 'python', 'Scripts') \
                if os.name == 'nt' else \
                os.path.join(lb_install, 'python', 'bin')
            if os.path.isdir(py_scripts):
                return py_scripts
        sys_dir = os.path.dirname(sys.executable)  # assume we are on some other cPython
        return os.path.join(sys_dir, 'Scripts') if os.name == 'nt' else sys_dir

    @property
    def python_exe_path(self):
        """Get the path to the Python executable to be used for Ladybug Tools CLI calls.

        If a version of Python is found within the ladybug_tools installation folder,
        this will be the path to that version of Python. Otherwise, it will be
        assumed that this is package is installed in cPython outside of the ladybug_tools
        folder and the sys.executable will be returned.
        """
        # check the ladybug_tools folder for a Python installation
        lb_install = self.ladybug_tools_folder
        if os.path.isdir(lb_install):
            py_exe_file = os.path.join(lb_install, 'python', 'python.exe') \
                if os.name == 'nt' else \
                os.path.join(lb_install, 'python', 'bin', 'python3')
            if os.path.isfile(py_exe_file):
                return py_exe_file
        return sys.executable  # assume we are on some other cPython

    @property
    def python_version(self):
        """Get a tuple for the version of python (eg. (3, 8, 2)).

        This will be None if the version could not be sensed or if no Python
        installation was found.
        """
        if self._python_version_str is None and self.python_exe_path:
            self._python_version_from_cli()
        return self._python_version

    @property
    def python_version_str(self):
        """Get text for the full version of python (eg."3.8.2").

        This will be None if the version could not be sensed or if no Python
        installation was found.
        """
        if self._python_version_str is None and self.python_exe_path:
            self._python_version_from_cli()
        return self._python_version_str

    @property
    def config_file(self):
        """Get or set the path to the config.json file from which folders are loaded.

        Setting this to None will result in using the config.json module included
        in this package.
        """
        return self._config_file

    @config_file.setter
    def config_file(self, cfg):
        if cfg is None:
            cfg = os.path.join(os.path.dirname(__file__), 'config.json')
        self._load_from_file(cfg)
        self._config_file = cfg

    def _load_from_file(self, file_path):
        """Set all of the the properties of this object from a config JSON file.

        Args:
            file_path: Path to a JSON file containing the file paths. A sample of this
                JSON is the config.json file within this package.
        """
        # check the default file path
        assert os.path.isfile(file_path), \
            ValueError('No file found at {}'.format(file_path))

        # set the default paths to be all blank
        default_path = {
            "ladybug_tools_folder": r'',
            "default_epw_folder": r''
        }

        with open(file_path, 'r') as cfg:
            try:
                paths = json.load(cfg)
            except Exception as e:
                print('Failed to load paths from {}.\nThey will be set to defaults '
                      'instead\n{}'.format(file_path, e))
            else:
                for key, p in paths.items():
                    if not key.startswith('__') and p.strip():
                        default_path[key] = p.strip()

        # set paths for the ladybug_tools_folder and default_epw_folder
        self.ladybug_tools_folder = default_path["ladybug_tools_folder"]
        self.default_epw_folder = default_path["default_epw_folder"]

    def _python_version_from_cli(self):
        """Set this object's Python version by making a call to a Python command."""
        cmds = [self.python_exe_path, '--version']
        use_shell = True if os.name == 'nt' else False
        process = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=use_shell)
        stdout = process.communicate()
        base_str = str(stdout[0]).replace("b'", '').replace(r"\r\n'", '')
        self._python_version_str = base_str.split(' ')[-1]
        try:
            self._python_version = \
                tuple(int(i) for i in self._python_version_str.split('.'))
        except Exception:
            pass  # failed to parse the version into values

    def _find_default_epw_folder(self):
        """Find the the default EPW folder in its usual location.

        An attempt will be made to create the directory if it does not already exist.
        """
        # first check if there's a user-defined folder in AppData
        app_folder = os.getenv('APPDATA')
        if app_folder is not None:
            epw_folder = os.path.join(app_folder, 'ladybug_tools', 'weather')
            if os.path.isdir(epw_folder):
                return epw_folder
        # if we're not on Windows, just use the ladybug_tools installation folder
        if os.name == 'nt' and app_folder is not None:
            pass
        else:
            epw_folder = os.path.join(self.ladybug_tools_folder, 'resources', 'weather')
        # create the folder if it does not exist
        if not os.path.isdir(epw_folder):
            try:
                os.makedirs(epw_folder)
            except Exception as e:
                raise OSError('Failed to create default epw '
                              'folder: %s\n%s' % (epw_folder, e))
        return epw_folder

    @staticmethod
    def _find_default_ladybug_tools_folder():
        """Find the the default ladybug_tools folder in its usual location.

        An attempt will be made to create the directory if it does not already exist.
        """
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        install_folder = os.path.join(home_folder, 'ladybug_tools')
        if not os.path.isdir(install_folder) or len(os.listdir(install_folder)) == 0:
            program_folder = os.getenv('PROGRAMFILES')
            if os.name == 'nt' and program_folder is not None and \
                    os.path.isdir(os.path.join(program_folder, 'ladybug_tools')):
                install_folder = os.path.join(program_folder, 'ladybug_tools')
            else:
                try:
                    os.makedirs(install_folder)
                except Exception as e:
                    # very rare case of an inaccessible HOME folder
                    # try to fall back on the Python installation folder of this package
                    current_path = os.path.normpath(__file__)
                    path_vars = current_path.split(os.sep)
                    all_path = []
                    for var in path_vars:
                        if 'python' in var.lower():
                            break
                        all_path.append(var)
                    if len(all_path) == len(path_vars):  # no Python identified
                        raise OSError(
                            'Failed to create default ladybug tools '
                            'installation folder: %s\n%s' % (install_folder, e))
                    all_path[0] = all_path[0] + os.sep
                    install_folder = os.path.join(*all_path)
        return install_folder


"""Object possessing all key folders within the configuration."""
folders = Folders()
