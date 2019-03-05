
![Ladybug](http://www.ladybug.tools/assets/img/ladybug.png)


[![Build Status](https://travis-ci.org/ladybug-tools/ladybug.svg?branch=master)](https://travis-ci.org/ladybug-tools/ladybug)
[![Coverage Status](https://coveralls.io/repos/github/ladybug-tools/ladybug/badge.svg?branch=master)](https://coveralls.io/github/ladybug-tools/ladybug)

[![Python 2.7](https://img.shields.io/badge/python-2.7-green.svg)](https://www.python.org/downloads/release/python-270/) [![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/) [![IronPython](https://img.shields.io/badge/ironpython-2.7-red.svg)](https://github.com/IronLanguages/ironpython2/releases/tag/ipy-2.7.8/)

# ladybug

Ladybug is a Python library to load, analyze and modify EneregyPlus Weather files (epw). You can download epw files from [EPWMap](http://www.ladybug.tools/epwmap/).

This repository includes the core library which is the base for Ladybug. For plugin-specific questions and comments refer to [ladybug-grasshopper](https://github.com/ladybug-tools/ladybug-grasshopper) or [ladybug-dynamo](https://github.com/ladybug-tools/ladybug-dynamo) repositories.

## note
For the legacy Ladybug Grasshopper plugin see [this repository](https://github.com/mostaphaRoudsari/ladybug).

## [API Documentation](http://ladybug-tools.github.io/apidoc/ladybug)

## Installation

`pip install lbt-ladybug`


## Usage

```python
# load epw weather data
from ladybug.epw import EPW
epw_data = EPW('path_to_epw_file')
dry_bulb_temp = epw_data.dry_bulb_temperature

# Get altitude and longitude
from ladybug.location import Location
form ladybug.sunpath import Sunpath

# Create location. You can also extract location data from an epw file.
sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22, time_zone=10)

# Initiate sunpath
sp = Sunpath.from_location(sydney)
sun = sp.calculate_sun(month=11, day=15, hour=11.0)

print('altitude: {}, azimuth: {}'.format(sun.altitude, sun.azimuth))
>>> altitude: 72.26, azimuth: 32.37
```


### derivative work
Ladybug is a derivative work of the following software projects:

[pyeuclid](https://code.google.com/p/pyeuclid/) for vector math calculation. Available under LGPL.

[PVLib-python](https://github.com/pvlib/pvlib-python) for solar irradiance calculations. Available under BSD 3-clause.

Applicable copyright notices for theses works can be found within the relevant .py files.
