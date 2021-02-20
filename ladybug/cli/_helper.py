"""A collection of helper functions used throughout the CLI.

Most functions assist with the serialization of objects to/from JSON.
"""
import json

from ladybug.analysisperiod import AnalysisPeriod


def _load_analysis_period_json(analysis_period_json):
    """Load an AnalysisPeriod from a JSON file.
    
    Args:
        analysis_period_json: A JSON file of an AnalysisPeriod to be loaded.
    """
    if analysis_period_json is not None and analysis_period_json != 'None':
        with open(analysis_period_json) as json_file:
            data = json.load(json_file)
        return AnalysisPeriod.from_dict(data)
