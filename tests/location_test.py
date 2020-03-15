# coding=utf-8
from ladybug.location import Location


def test_init():
    """Test if the command correctly creates location based on individual values"""
    # This is totally a real place! It's in Wales, check it out!
    city = 'Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch'
    country = 'United Kingdom'
    latitude = 53.2225252
    longitude = -4.2211707
    time_zone = 1
    elevation = 12
    station_id = 'SomeInventedStation'
    source = 'SomeNoneExistentSource'

    loc = Location(city=city, country=country, latitude=latitude,
                   longitude=longitude, time_zone=time_zone,
                   elevation=elevation, station_id=station_id, source=source)

    str(loc)  # test the string representation
    assert loc.city == city
    assert loc.country == country
    assert loc.latitude == latitude
    assert loc.longitude == longitude
    assert loc.time_zone == time_zone
    assert loc.elevation == elevation
    assert loc.station_id == station_id
    assert loc.source == source
    assert loc.meridian == -15


def test_default_values():
    """Test if the command correctly creates a location."""
    loc = Location()
    assert loc.city == '-'
    assert loc.country == '-'
    assert loc.latitude == 0
    assert loc.longitude == 0
    assert loc.time_zone == 0
    assert loc.station_id is None
    assert loc.source is None


def test_from_individual_values():
    """Test if the command correctly creates location based on individual values"""
    loc = Location()

    new_latitude = 31.4234953
    new_longitude = 72.9492158
    new_time_zone = 5
    new_elevation = 20

    loc.latitude = new_latitude
    loc.longitude = new_longitude
    loc.time_zone = new_time_zone
    loc.elevation = new_elevation

    assert loc.latitude == new_latitude
    assert loc.longitude == new_longitude
    assert loc.time_zone == new_time_zone
    assert loc.elevation == new_elevation


def test_from_location():
    """Test the from_location() class method"""
    city = 'Tehran'
    country = 'Iran'
    latitude = 36
    longitude = 34
    time_zone = 3.5
    elevation = 54

    loc = Location(city=city, country=country, latitude=latitude,
                   longitude=longitude, time_zone=time_zone,
                   elevation=elevation)

    loc_from_loc = Location.from_location(loc)

    assert loc_from_loc.city == city
    assert loc_from_loc.country == country
    assert loc_from_loc.latitude == latitude
    assert loc_from_loc.longitude == longitude
    assert loc_from_loc.time_zone == time_zone
    assert loc_from_loc.elevation == elevation


def test_dict_methods():
    """Test JSON serialization functions"""
    city = 'Tehran'
    country = 'Iran'
    latitude = 36
    longitude = 34
    time_zone = 3.5
    elevation = 54

    loc = Location(city=city, country=country, latitude=latitude,
                   longitude=longitude, time_zone=time_zone,
                   elevation=elevation)

    assert loc.to_dict() == {"city": city, "state": '-', "country": country,
                             "latitude": latitude, "longitude": longitude,
                             "time_zone": time_zone, "elevation": elevation,
                             "station_id": None, "source": None, "type": 'Location'}

    loc_from_dict = Location.from_dict(loc.to_dict())

    assert loc_from_dict.city == city
    assert loc_from_dict.latitude == latitude
    assert loc_from_dict.longitude == longitude
    assert loc_from_dict.time_zone == time_zone
    assert loc_from_dict.elevation == elevation
    assert loc_from_dict.country == country


def test_idf_methods():
    """Test the to/from idf methods."""
    loc = Location('Tehran', '', 'Iran', 36, 34, 3.5, 54)
    loc_idf = loc.to_idf()
    new_idf = Location.from_idf(loc_idf)
    assert loc_idf == new_idf.to_idf()


def test_duplicate():
    """Test the duplicate method."""
    city = 'Tehran'
    country = 'Iran'
    latitude = 36
    longitude = 34
    time_zone = 3.5
    elevation = 54

    loc = Location(city=city, country=country, latitude=latitude,
                   longitude=longitude, time_zone=time_zone,
                   elevation=elevation)
    loc_dup = loc.duplicate()

    assert loc.city == loc_dup.city == city
    assert loc.country == loc_dup.country == country
    assert loc.latitude == loc_dup.latitude == latitude
    assert loc.longitude == loc_dup.longitude == longitude
    assert loc.time_zone == loc_dup.time_zone == time_zone
    assert loc.elevation == loc_dup.elevation == elevation
