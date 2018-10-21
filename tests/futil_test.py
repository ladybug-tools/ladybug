# coding=utf-8

import unittest
import os

import ladybug.futil as futil


class DataCollectionTestCase(unittest.TestCase):
    """Test for (ladybug/futil.py)"""

    # preparing to test.
    def setUp(self):
        """set up."""

    def tearDown(self):
        """Nothing to tear down as nothing gets written to file."""
        pass

    def test_download_file(self):
        """Test the download file capability"""
        wf_url = "https://www.energyplus.net/weather-download/" \
            "southwest_pacific_wmo_region_5/AUS//AUS_NSW.Sydney.947670_IWEC/all"
        wf_name = os.path.join("./tests/zip", "AUS_NSW.Sydney.947670_IWEC.zip")
        futil.download_file(wf_url, wf_name)
        assert os.path.isfile(wf_name)

    def test_unzip_file(self):
        """Test the unzip file capability"""
        folder = "./tests/zip/extracted"
        wf_path = "./tests/zip/test.zip"
        futil.unzip_file(wf_path, folder)
        extracted_epw = os.path.join(folder, "AUS_NSW.Sydney.947670_IWEC.epw")
        assert os.path.isfile(extracted_epw)
        futil.nukedir(folder)

    def test_copy_files_to_folder(self):
        """Test the copy file to folder capability"""
        existing_file = "./tests/ddy/chicago.ddy"
        target_dir = "./tests/zip"
        futil.copy_files_to_folder([existing_file], target_dir)
        final_file = os.path.join(target_dir, "chicago.ddy")
        assert os.path.isfile(final_file)
        os.remove(final_file)


if __name__ == "__main__":
    unittest.main()