"""Honeybee configurations.

Import this module in every module that you need to access Honeybee configurations.

Usage:

    import config
    print(config.radlib_path)
    print(config.radbin_path)
    print(config.platform)
    config.radbin_path = "c:/radiance/bin"
"""
import os
import sys
import json


class Folders(object):
    """Honeybee folders.

    Attributes:
        mute: Set to True if you don't want the class to print the report
            (Default: False)

    Usage:

        folders = Folders(mute=False)
        print(folders.radbin_path)
    """

    __defaultPath = {
        "path_to_radiance": r'',
        "path_to_energyplus": r'',
        "path_to_openstudio": r'',
        "path_to_perl": r''
    }

    __configFile = os.path.join(os.path.dirname(__file__), 'config.json')

    def __init__(self, mute=False):
        """Find default path for Honeybee.

        It currently includes:
            Default path to Radinace folders.
            Default path to EnergyPlus folders.
        """
        self.mute = mute

        # try to load paths from config file
        self.load_from_file()

        # set path for openstudio
        self.open_studio_path = self.__defaultPath["path_to_openstudio"]

        # set path for radiance, if path to radiance is not set honeybee will
        # try to set it up to the radiance installation that comes with openStudio
        self.radiance_path = self.__defaultPath["path_to_radiance"]
        self.perl_path = self.__defaultPath["path_to_perl"]

    @staticmethod
    def _which(program):
        """Find executable programs.

        Args:
            program: Full file name for the program (e.g. rad.exe)

        Returns:
            File directory and full path to program in case of success.
            None, None in case of failure.
        """
        def is_exe(fpath):
            # Make sure it's not part of Dive installation as DIVA doesn't
            # follow the standard structure folder for Daysim and Radiance
            if os.name == 'nt' and fpath.upper().find("DIVA"):
                return False

            # Return true if file exists and is executable
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        # check for the file in all path in environment
        for path in os.environ["PATH"].split(os.pathsep):
            # strip "" from Windows path
            exe_file = os.path.join(path.strip('"'), program)
            if is_exe(exe_file):
                return path, exe_file

        # couldn't find it! return None :|
        return None, None

    @property
    def open_studio_path(self):
        """Set and get the path to openstudio installation folder."""
        return self._open_studio_path

    @open_studio_path.setter
    def open_studio_path(self, path):
        if not path:
            # check the default installation folders on Windows
            path = self._find_open_studio_folder()

        self._open_studio_path = path
        if os.name == 'nt' and self._open_studio_path:
            assert os.path.isfile(os.path.join(path, 'bin/openstudio.exe')), \
                '{} is not a valid path to openstudio installation.'.format(path)
            if not self.mute and self._open_studio_path:
                print("Path to OpenStudio is set to: %s" % self._open_studio_path)

    # TODO(mostapha or chris): Update for OpenStudio 2
    @staticmethod
    def _find_open_studio_folder():

        def getversion(open_studio_path):
            ver = ''.join(s for s in open_studio_path if (s.isdigit() or s == '.'))
            return sum(int(i) * d ** 10 for d, i in enumerate(reversed(ver.split('.'))))

        if os.name == 'nt':
            os_folders = ['C:/Program Files/' + f for f
                          in os.listdir('C:/Program Files')
                          if (f.lower().startswith('openstudio') and
                              os.path.isdir('C:/Program Files/' + f))]
            if not os_folders:
                return
            return sorted(os_folders, key=getversion, reverse=True)[0]
        else:
            return

    @property
    def radiance_path(self):
        """Get and set path to radiance installation folder."""
        return self._radiancePath

    @property
    def radbin_path(self):
        """Path to Radiance binary folder."""
        return self._radbin

    @property
    def radlib_path(self):
        """Path to Radiance library folder."""
        return self._radlib

    @radiance_path.setter
    def radiance_path(self, path):
        if not path:
            if os.name == 'nt':
                __radbin, __rad_file = self._which("rad.exe")
                if __radbin:
                    path = os.path.split(__radbin)[0]
                # finding by path failed. Let's check typical folders on Windows
                elif os.path.isfile(r"c:/radiance/bin/rad.exe"):
                    path = r"c:/radiance"
                elif os.path.isfile(r"c:/Program Files/radiance/bin/rad.exe"):
                    path = r"c:/Program Files/radiance"
                elif self.open_studio_path and os.path.isfile(
                        os.path.join(self.open_studio_path,
                                     r"share/openStudio/Radiance/bin/rad.exe")):
                    path = os.path.join(self.open_studio_path,
                                        r"share/openStudio/Radiance")
            elif os.name == 'posix':
                __radbin, __rad_file = self._which("mkillum")
                if __radbin:
                    path = os.path.split(__radbin)[0]

        self._radiancePath = path

        if not os.path.isdir(path):
            if not self.mute:
                msg = "Warning: Failed to find radiance installation folder.\n" \
                    "You can set it up manually in {}.".format(self.__configFile)
                print(msg)
            self._radbin = ""
            self._radlib = ""
        else:
            # set up lib path
            self._radbin = os.path.normpath(os.path.join(path, 'bin'))
            self._radlib = os.path.normpath(os.path.join(path, 'lib'))

            if not self.mute and self._radiancePath:
                print("Path to radiance is set to: %s" % self._radiancePath)

            if self._radiancePath.find(' ') != -1:
                msg = 'Radiance path {} has a whitespace. Some of the radiance ' \
                    'commands may fail.\nWe strongly suggest you to install radiance ' \
                    'under a path with no withspace (e.g. c:/radiance)'.format(
                        self._radiancePath
                    )
                print(msg)

    @property
    def perl_path(self):
        """Path to the folder containing Perl binary files."""
        return self._perl_path

    @property
    def perl_exe_path(self):
        """Path to perl executable file."""
        return self._perlExePath

    @perl_path.setter
    def perl_path(self, path):
        """Path to the folder containing Perl binary files."""
        self._perl_path = path or ""
        self._perlExePath = path + "/perl"

        if not self._perl_path:
            if os.name == 'nt':
                self._perl_path, self._perlExePath = self._which("perl.exe")
            elif os.name == 'posix':
                self._perl_path, self._perlExePath = self._which("perl")

        if not self._perl_path and self.open_studio_path:
            # try to find perl under openstudio
            p = os.path.join(self.open_studio_path,
                             'strawberry-perl-5.16.2.1-32bit-portable-reduced')
            if os.path.isfile(os.path.join(p, 'perl/bin/perl.exe')):
                self._perl_path, self._perlExePath = p, \
                    os.path.join(p, 'perl/bin/perl.exe')

        if not self.mute and self._perl_path:
            print("Path to perl is set to: %s" % self._perl_path)

    @property
    def ep_folder(self):
        """Path to EnergyPlus folder."""
        raise NotImplementedError
        # return self._eplus

    @property
    def python_exe_path(self):
        """Path to Python folder."""
        return sys.executable

    def load_from_file(self, file_path=None):
        """Load installation folders from a json file."""
        file_path = file_path or self.__configFile
        assert os.path.isfile(str(file_path)), \
            ValueError('No such a file as {}'.format(file_path))

        with open(file_path, 'rb') as cfg:
            path = cfg.read().replace('\\\\', '/').replace('\\', '/')
            try:
                paths = json.loads(path)
            except Exception:
                print('Failed to load paths from {}.'.format(file_path))
            else:
                for key, p in paths.iteritems():
                    if not key.startswith('__') and p.strip():
                        self.__defaultPath[key] = p.strip()


f = Folders(mute=False)

radlib_path = f.radlib_path
"""Path to Radinace libraries folder."""

radbin_path = f.radbin_path
"""Path to Radinace binaries folder."""

# NotImplemented yet
ep_path = None
"""Path to EnergyPlus folder."""

perl_exe_path = f.perl_exe_path
"""Path to the perl executable needed for some othe Radiance Scripts."""


python_exe_path = f.python_exe_path
"""Path to python executable needed for some Radiance scripts from the PyRad
library"""

wrapper = "\"" if os.name == 'nt' else "'"
"""Wrapper for path with white space."""
