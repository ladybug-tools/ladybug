# coding=utf-8
import ladybug.futil as futil

import pytest
import os


def test_unzip_file():
    """Test the unzip file capability"""
    folder = "./tests/assets/zip/extracted"
    wf_path = "./tests/assets/zip/test.zip"
    futil.unzip_file(wf_path, folder)
    extracted_epw = os.path.join(folder, "AUS_NSW.Sydney.947670_IWEC.epw")
    assert os.path.isfile(extracted_epw)
    assert 1500000 < os.stat(extracted_epw).st_size < 1600000
    futil.nukedir(folder)


def test_copy_files_to_folder():
    """Test the copy file to folder capability"""
    existing_file = "./tests/assets/ddy/chicago.ddy"
    target_dir = "./tests/assets/zip"
    futil.copy_files_to_folder([existing_file], target_dir)
    final_file = os.path.join(target_dir, "chicago.ddy")
    assert os.path.isfile(final_file)
    assert 20000 < os.stat(final_file).st_size < 30000
    os.remove(final_file)


def test_csv_to_matrix():
    """Test the csv_to_matrix functions."""
    path = './tests/assets/epw/tokyo.epw'
    epw_mtx = futil.csv_to_matrix(path)
    assert len(epw_mtx) == 8768

    with pytest.raises(Exception):
        epw_mtx = futil.csv_to_num_matrix(path)
