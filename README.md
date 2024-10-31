
![Ladybug](http://www.ladybug.tools/assets/img/ladybug.png)

[![Build Status](https://github.com/ladybug-tools/ladybug/workflows/CI/badge.svg)](https://github.com/ladybug-tools/ladybug/actions)
[![Coverage Status](https://coveralls.io/repos/github/ladybug-tools/ladybug/badge.svg?branch=master)](https://coveralls.io/github/ladybug-tools/ladybug)

[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![Python 2.7](https://img.shields.io/badge/python-2.7-green.svg)](https://www.python.org/downloads/release/python-270/) [![IronPython](https://img.shields.io/badge/ironpython-2.7-red.svg)](https://github.com/IronLanguages/ironpython2/releases/tag/ipy-2.7.8/)

# ladybug

Ladybug is a Python library to analyze, modify, and visualize EnergyPlus Weather files (epw). You can download epw files from [EPWMap](http://www.ladybug.tools/epwmap/).

This repository is the core library that is the base for the Ladybug Grasshopper Plugin. For plugin-specific questions and comments refer to [ladybug-grasshopper](https://github.com/ladybug-tools/ladybug-grasshopper).

## Note

For the Legacy Ladybug Grasshopper Plugin see [this repository](https://github.com/ladybug-tools/ladybug-legacy).

## [API Documentation](https://www.ladybug.tools/ladybug/docs/)

## Installation

To install the library use:

`pip install ladybug-core`

To check if Honeybee command line interface is installed correctly use `ladybug viz` and you
should get a `viiiiiiiiiiiiizzzzzzzzz!` back in response!

## Usage

```python
# load epw weather data
from ladybug.epw import EPW
epw_data = EPW('path_to_epw_file')
dry_bulb_temp = epw_data.dry_bulb_temperature

# Get altitude and longitude
from ladybug.location import Location
from ladybug.sunpath import Sunpath

# Create location. You can also extract location data from an epw file.
sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22, time_zone=10)

# Initiate sunpath
sp = Sunpath.from_location(sydney)
sun = sp.calculate_sun(month=11, day=15, hour=11.0)

print('altitude: {}, azimuth: {}'.format(sun.altitude, sun.azimuth))
>>> altitude: 72.26, azimuth: 32.37
```

## Local Development
1. Clone this repo locally
```console
git clone git@github.com:ladybug-tools/ladybug.git

# or

git clone https://github.com/ladybug-tools/ladybug.git
```
2. Install dependencies:
```console
cd ladybug
pip install -r dev-requirements.txt
pip install -r requirements.txt
```

3. Run Tests:
```console
python -m pytest ./tests
```

4. Generate Documentation:
```console
sphinx-apidoc -f -e -d 4 -o ./docs ./ladybug
sphinx-build -b html ./docs ./docs/_build/docs
```

### Derivative Work

Ladybug is a derivative work of the following software projects:

* [PVLib-python](https://github.com/pvlib/pvlib-python) for solar irradiance calculations. Available under BSD 3-clause.
* [PsychroLib](https://github.com/psychrometrics/psychrolib) for psychrometric calculations. Available under MIT License.

Applicable copyright notices for these works can be found within the relevant .py files.
