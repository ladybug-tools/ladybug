[![Build Status](https://travis-ci.org/AntoineDao/ladybug.svg?branch=master)](https://travis-ci.org/AntoineDao/ladybug)
[![Coverage Status](https://coveralls.io/repos/github/AntoineDao/ladybug/badge.svg)](https://coveralls.io/github/AntoineDao/ladybug)

![Ladybug](http://www.ladybug.tools/assets/img/ladybug.png)

# ladybug

Ladybug is a Python library to load, analyze and modify EneregyPlus Weather files (epw). You can download epw files from [EPWMap](http://www.ladybug.tools/epwmap/).

This repository includes the core library which is the base for Ladybug. For plugin-specific questions and comments refer to [ladybug-grasshopper](https://github.com/ladybug-tools/ladybug-grasshopper) or [ladybug-dynamo](https://github.com/ladybug-tools/ladybug-dynamo) repositories.

Check [this repository](https://github.com/mostaphaRoudsari/ladybug) for the legacy ladybug plugin for Grasshopper.

## [API Documentation](http://ladybug-tools.github.io/apidoc/ladybug)

## Usage

```python
# load epw weather data
from ladybug.epw import EPW
epw_data = EPW('path_to_epw_file')
dry_bulb_temp = epw_data.dry_bulb_temperature

# Get altitude and longitude
from ladybug.location import Location
form ladybug.sunpath import Sunpath
# You can also get the location from epw file if available
sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22,
                  time_zone=10)
sp = Sunpath.from_location(sydney)
sun = sp.calculate_sun(month=11, day=15, hour=11.0)
print('altitude: {}, azimuth: {}'.format(sun.altitude, sun.azimuth))
>>> altitude: 72.26, azimuth: 32.37
```


### dependencies
[pyeuclid](https://code.google.com/p/pyeuclid/) for vector math calculation. It's available under LGPL.
