"""Utilities for serializing Data Collections to and from files."""
import os
import json

from ladybug.dt import DateTime
try:  # check if we are in IronPython
    import cPickle as pickle
except ImportError:  # wea re in cPython
    import pickle

from .datacollection import BaseCollection, HourlyDiscontinuousCollection, \
    HourlyContinuousCollection, DailyCollection, MonthlyCollection, \
    MonthlyPerHourCollection
from .header import Header
from .analysisperiod import AnalysisPeriod
from .dt import Date


def collections_to_csv(data_collections, folder, file_name='data.csv'):
    """Write a series of aligned Data Collections into a CSV.

    These can be serialized back to the original objects using the
    collections_from_csv method.

    Args:
        data_collections: A list of aligned Data Collections which will be
            written to a CSV.
        folder: Folder to which the CSV will be written.
        file_name: File name for the CSV (Default: data.csv).

    Returns:
        The path to the CSV file to which the data_collections have been written.
    """
    # check that the collections are aligned with each other
    assert BaseCollection.are_collections_aligned(data_collections, False), \
        'Data collections must be aligned with each other in order to ' \
        'use collections_to_csv.'
    header_len = 2 + len(data_collections[0].header.metadata) \
        if BaseCollection.are_metadatas_aligned(data_collections, False) else 3
    csv_data = []

    # create the first column with the datetimes
    dt_column = [''] * (header_len - 2)
    dt_column.append(data_collections[0]._collection_type)
    dt_column.append(str(data_collections[0].header.analysis_period))
    dt_column.extend(data_collections[0].datetime_strings)
    csv_data.append(dt_column)

    # loop through the data collections and add columns for each
    meta_per_row = False if header_len == 3 else True
    for dat in data_collections:
        dat_column = dat.header.to_csv_strings(meta_per_row)
        dat_column.extend([str(v) for v in dat.values])
        csv_data.append(dat_column)

    # dump all of the data into the CSV file
    if not os.path.isdir(folder):
        os.makedirs(folder)
    if not file_name.lower().endswith('.csv'):
        file_name += '.csv'
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'w') as outf:
        for row in zip(*csv_data):
            outf.write(','.join(row) + '\n')
    return file_path


def collections_from_csv(data_file):
    """Load a series of Data Collections from a JSON file.

    Args:
        data_file: Path to a .json file containing a list of data collections.

    Returns:
        A list of data collections loaded from the .json file.
    """
    # perform checks and set variables to help with re-serialization
    assert os.path.isfile(data_file), 'Failed to find %s' % data_file
    coll_types = {
        'HourlyContinuous': HourlyContinuousCollection,
        'HourlyDiscontinuous': HourlyDiscontinuousCollection,
        'Monthly': MonthlyCollection,
        'Daily': DailyCollection,
        'MonthlyPerHour': MonthlyPerHourCollection
    }

    # load all of the data from the file
    headers, values, datetimes, coll_class, aper = [], [], [], None, None
    with open(data_file) as inf:
        # first load all of the header information
        for row in inf:
            row_data = row.strip().split(',')
            headers.append(row_data[1:])
            if row_data[0] in coll_types:
                coll_class = coll_types[row_data[0]]
            elif coll_class is not None:
                aper = AnalysisPeriod.from_string(row_data[0])
                break
        # then, load all of the values and datetimes
        for row in inf:
            row_data = row.split(',')
            datetimes.append(row_data[0])
            values.append([float(v) for v in row_data[1:]])

    # reconstruct data collections from the loaded data
    heads = [Header.from_csv_strings(h, aper) for h in zip(*headers)]
    t_vals = zip(*values)
    if coll_class == HourlyContinuousCollection:
        data = [HourlyContinuousCollection(h, v) for h, v in zip(heads, t_vals)]
    elif coll_class == HourlyDiscontinuousCollection:
        dts = [DateTime.from_date_time_string(d) for d in datetimes]
        data = [HourlyDiscontinuousCollection(h, v, dts) for h, v in zip(heads, t_vals)]
    elif coll_class == MonthlyCollection:
        inv_map = {v: k for k, v in AnalysisPeriod.MONTHNAMES.items()}
        dts = [inv_map[d] for d in datetimes]
        data = [MonthlyCollection(h, v, dts) for h, v in zip(heads, t_vals)]
    elif coll_class == DailyCollection:
        dts = [Date.from_date_string(d, aper.is_leap_year) for d in datetimes]
        data = [DailyCollection(h, v, dts) for h, v in zip(heads, t_vals)]
    elif coll_class == MonthlyPerHourCollection:
        inv_map = {v: k for k, v in AnalysisPeriod.MONTHNAMES.items()}
        dt_strs = [d.split(' ') for d in datetimes]
        dts = [(inv_map[d[0]], int(d[1].split(':')[0]), int(d[1].split(':')[1]))
               for d in dt_strs]
        data = [MonthlyPerHourCollection(h, v, dts) for h, v in zip(heads, t_vals)]
    for d in data:
        d._validated_a_period = True
    return data


def collections_to_json(data_collections, folder, file_name='data.json', indent=None):
    """Write a series of Data Collections into a JSON.

    These can be serialized back to the original objects using the
    collections_from_json method.

    Args:
        data_collections: A list of aligned Data Collections which will be
            written to a JSON.
        folder: Folder to which the JSON will be written.
        file_name: File name for the JSON (Default: data.json).
        indent: A positive integer to set the indentation used in the resulting
            JSON file. (Default: None).

    Returns:
        The path to the JSON file to which the data_collections have been written.
    """
    # convert the data collections to an array of dictionaries
    dat_dict = [dat.to_dict() for dat in data_collections]
    # dump all of the data into the JSON file
    if not os.path.isdir(folder):
        os.makedirs(folder)
    if not file_name.lower().endswith('.json'):
        file_name += '.json'
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'w') as fp:
        json.dump(dat_dict, fp, indent=indent)
    return file_path


def collections_from_json(data_file):
    """Load a series of Data Collections from a JSON file.

    Args:
        data_file: Path to a .json file containing a list of data collections.

    Returns:
        A list of data collections loaded from the .json file.
    """
    assert os.path.isfile(data_file), 'Failed to find %s' % data_file
    with open(data_file) as inf:
        data = json.load(inf)
    return [_dict_to_collection(d_dict) for d_dict in data]


def collections_to_pkl(data_collections, folder, file_name='data.pkl'):
    """Write a series of Data Collections into a PKL.

    These can be serialized back to the original objects using the
    collections_from_pkl method.

    Args:
        data_collections: A list of aligned Data Collections which will be
            written to a PKL.
        folder: Folder to which the PKL will be written.
        file_name: File name for the PKL (Default: data.pkl).
        indent: A positive integer to set the indentation used in the resulting
            PKL file. (Default: None).

    Returns:
        The path to the PKL file to which the data_collections have been written.
    """
    # convert the data collections to an array of dictionaries
    dat_dict = [dat.to_dict() for dat in data_collections]
    # dump all of the data into the PKL file
    if not os.path.isdir(folder):
        os.makedirs(folder)
    if not file_name.lower().endswith('.pkl'):
        file_name += '.pkl'
    file_path = os.path.join(folder, file_name)
    with open(file_path, 'wb') as fp:
        pickle.dump(dat_dict, fp)
    return file_path


def collections_from_pkl(data_file):
    """Load a series of Data Collections from a PKL file.

    Args:
        data_file: Path to a .pkl file containing a list of data collections.

    Returns:
        A list of data collections loaded from the .pkl file.
    """
    assert os.path.isfile(data_file), 'Failed to find %s' % data_file
    with open(data_file, 'rb') as inf:
        data = pickle.load(inf)
    return [_dict_to_collection(d_dict) for d_dict in data]


def _dict_to_collection(data_dict):
    """Load any data collection dictionary to an object."""
    if data_dict['type'] == 'HourlyContinuous':
        return HourlyContinuousCollection.from_dict(data_dict)
    elif data_dict['type'] == 'HourlyDiscontinuous':
        return HourlyDiscontinuousCollection.from_dict(data_dict)
    elif data_dict['type'] == 'Monthly':
        return MonthlyCollection.from_dict(data_dict)
    elif data_dict['type'] == 'Daily':
        return DailyCollection.from_dict(data_dict)
    elif data_dict['type'] == 'MonthlyPerHour':
        return MonthlyPerHourCollection.from_dict(data_dict)
    else:
        raise ValueError(
            'Unrecognized data collection type "{}".'.format(data_dict['type']))
