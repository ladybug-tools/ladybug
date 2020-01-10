# coding=utf-8
from ladybug.dt import DateTime, Date, Time
import pickle


def test_date_time_init():
    """Test the init method for DateTime and basic properties."""
    dt1 = DateTime(6, 21, 12)
    dt2 = DateTime(6, 21, 12)
    dt3 = DateTime(6, 21, 12, leap_year=True)
    dt4 = DateTime(6, 21, 13)
    str(dt1)  # test the string representation of Datetime

    assert dt1.month == 6
    assert dt1.day == 21
    assert dt1.hour == 12
    assert dt1.minute == 0
    assert not dt1.leap_year
    assert dt1.doy == 172
    assert dt1.hoy == 4116
    assert dt1.moy == 246960
    assert isinstance(dt1.int_hoy, int)
    assert dt1.int_hoy == 4116
    assert dt1.float_hour == 12.0
    assert dt1.date == Date(6, 21)
    assert dt1.time == Time(12, 0)

    assert dt1 == dt2
    assert dt1 != dt3
    assert dt1 != dt4

    assert sorted([dt4, dt1]) == [dt1, dt4]


def test_date_time_to_from_dict():
    """Test the dict methods for DateTime."""
    dt1 = DateTime(6, 21, 12)
    dt_dict = dt1.to_dict()
    rebuilt_dt = DateTime.from_dict(dt_dict)
    assert dt1 == rebuilt_dt
    assert rebuilt_dt.to_dict() == dt_dict


def test_to_from_date_time_string():
    """Test the from_date_time_string method for DateTime."""
    dt1 = DateTime(6, 21, 12)
    dt_str = str(dt1)
    rebuilt_dt = DateTime.from_date_time_string(dt_str)
    assert rebuilt_dt == dt1
    assert str(rebuilt_dt) == dt_str


def test_to_from_array():
    """Test the from_array method for DateTime."""
    dt1 = DateTime(6, 21, 12)
    dt_arr = dt1.to_array()
    rebuilt_dt = DateTime.from_array(dt_arr)
    assert rebuilt_dt == dt1
    assert rebuilt_dt.to_array() == dt_arr


def test_date_time_from_hoy():
    """Test the from_hoy method for DateTime and basic properties."""
    dt1 = DateTime.from_hoy(4116)
    assert dt1 == DateTime(6, 21, 12)
    dt2 = DateTime.from_hoy(4116, leap_year=True)
    assert dt2 == DateTime(6, 20, 12, leap_year=True)


def test_date_time_from_moy():
    """Test the from_moy method for DateTime and basic properties."""
    dt1 = DateTime.from_moy(246960)
    assert dt1 == DateTime(6, 21, 12)
    dt2 = DateTime.from_moy(246960, leap_year=True)
    assert dt2 == DateTime(6, 20, 12, leap_year=True)


def test_date_time_add_sub():
    """Test the add and subtract methods for DateTime."""
    dt1 = DateTime(6, 21, 12)
    dt2 = dt1.add_hour(1)
    dt3 = dt1.sub_hour(1)
    dt4 = dt1.add_minute(1)
    dt5 = dt1.sub_minute(1)

    assert dt2 == DateTime(6, 21, 13)
    assert dt3 == DateTime(6, 21, 11)
    assert dt4 == DateTime(6, 21, 12, 1)
    assert dt5 == DateTime(6, 21, 11, 59)


def test_date_init():
    """Test the init method for Date and basic properties."""
    dt1 = Date(6, 21)
    dt2 = Date(6, 21)
    dt3 = Date(6, 21, leap_year=True)
    dt4 = Date(6, 22)
    str(dt1)  # test the string representation of Date

    assert dt1.month == 6
    assert dt1.day == 21
    assert not dt1.leap_year
    assert dt1.doy == 172

    assert dt1 == dt2
    assert dt1 != dt3
    assert dt1 != dt4

    assert sorted([dt4, dt1]) == [dt1, dt4]


def test_date_from_doy():
    """Test the from_doy method for Date and basic properties."""
    dt1 = Date.from_doy(172)
    assert dt1 == Date(6, 21)
    dt2 = Date.from_doy(172, leap_year=True)
    assert dt2 == Date(6, 20, leap_year=True)
    dt3 = Date.from_doy(181)
    assert dt3 == Date(6, 30)
    dt4 = Date.from_doy(182)
    assert dt4 == Date(7, 1)


def test_date_to_from_dict():
    """Test the dict methods for Date."""
    dt1 = Date(6, 21)
    dt_dict = dt1.to_dict()
    rebuilt_dt = Date.from_dict(dt_dict)
    assert dt1 == rebuilt_dt
    assert rebuilt_dt.to_dict() == dt_dict


def test_to_from_date_string():
    """Test the from_date_string method for Date."""
    dt1 = Date(6, 21)
    dt_str = str(dt1)
    rebuilt_dt = Date.from_date_string(dt_str)
    assert rebuilt_dt == dt1
    assert str(rebuilt_dt) == dt_str


def test_date_to_from_array():
    """Test the from_array method for Date."""
    dt1 = Date(6, 21)
    dt_arr = dt1.to_array()
    rebuilt_dt = Date.from_array(dt_arr)
    assert rebuilt_dt == dt1
    assert rebuilt_dt.to_array() == dt_arr


def test_time_init():
    """Test the init method for Date and basic properties."""
    t1 = Time(12, 30)
    t2 = Time(12, 30)
    t3 = Time(12, 31)
    str(t1)  # test the string representation of Time

    assert t1.hour == 12
    assert t1.minute == 30
    assert t1.mod == 750

    assert t1 == t2
    assert t1 != t3

    assert sorted([t3, t1]) == [t1, t3]


def test_time_from_mod():
    """Test the from_mod method for Time and basic properties."""
    t1 = Time.from_mod(750)
    assert t1 == Time(12, 30)


def test_time_to_from_dict():
    """Test the dict methods for Time."""
    t1 = Time(12, 30)
    t_dict = t1.to_dict()
    rebuilt_t = Time.from_dict(t_dict)
    assert t1 == rebuilt_t
    assert rebuilt_t.to_dict() == t_dict


def test_to_from_time_string():
    """Test the from_time_string method for Time."""
    t1 = Time(12, 30)
    t_str = str(t1)
    rebuilt_t = Time.from_time_string(t_str)
    assert rebuilt_t == t1
    assert str(rebuilt_t) == t_str


def test_time_to_from_array():
    """Test the from_array method for Date."""
    t1 = Time(12, 30)
    t_arr = t1.to_array()
    rebuilt_t = Time.from_array(t_arr)
    assert rebuilt_t == t1
    assert rebuilt_t.to_array() == t_arr


def test_pickle_and_unpickle():
    """Test the pickling and unpickling of DateTime, Date, and Time objects."""
    dt1 = DateTime(6, 21, 12)
    dt2 = Date(6, 21)
    dt3 = Time(12, 30)

    serialized_dt1 = pickle.dumps(dt1)
    serialized_dt2 = pickle.dumps(dt2)
    serialized_dt3 = pickle.dumps(dt3)

    assert pickle.loads(serialized_dt1) == dt1
    assert pickle.loads(serialized_dt2) == dt2
    assert pickle.loads(serialized_dt3) == dt3
