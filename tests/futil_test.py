# coding=utf-8
import ladybug.futil as futil

import pytest
import os


def test_download_file():
    """Test the download file capability"""
    wf_url = "https://www.energyplus.net/weather-download/" \
        "southwest_pacific_wmo_region_5/AUS//AUS_NSW.Sydney.947670_IWEC/all"
    wf_name = os.path.join("./tests/fixtures/zip", "AUS_NSW.Sydney.947670_IWEC.zip")
    futil.download_file(wf_url, wf_name)
    assert os.path.isfile(wf_name)
    assert 200000 < os.stat(wf_name).st_size < 300000
    os.remove(wf_name)


def test_unzip_file():
    """Test the unzip file capability"""
    folder = "./tests/fixtures/zip/extracted"
    wf_path = "./tests/fixtures/zip/test.zip"
    futil.unzip_file(wf_path, folder)
    extracted_epw = os.path.join(folder, "AUS_NSW.Sydney.947670_IWEC.epw")
    assert os.path.isfile(extracted_epw)
    assert 1500000 < os.stat(extracted_epw).st_size < 1600000
    futil.nukedir(folder)


def test_copy_files_to_folder():
    """Test the copy file to folder capability"""
    existing_file = "./tests/fixtures/ddy/chicago.ddy"
    target_dir = "./tests/fixtures/zip"
    futil.copy_files_to_folder([existing_file], target_dir)
    final_file = os.path.join(target_dir, "chicago.ddy")
    assert os.path.isfile(final_file)
    assert 20000 < os.stat(final_file).st_size < 30000
    os.remove(final_file)


def test_csv_to_matrix():
    """Test the csv_to_matrix functions."""
    path = './tests/fixtures/epw/tokyo.epw'
    epw_mtx = futil.csv_to_matrix(path)
    assert len(epw_mtx) == 8768

    with pytest.raises(Exception):
        epw_mtx = futil.csv_to_num_matrix(path)
