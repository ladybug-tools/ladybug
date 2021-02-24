"""A collection of helper functions used throughout the CLI.

Most functions assist with the serialization of objects to/from JSON.
"""
import json

from ladybug.analysisperiod import AnalysisPeriod


def _load_analysis_period_str(analysis_period_str):
    """Load an AnalysisPeriod from a JSON file.
    
    Args:
        analysis_period_str: A JSON file of an AnalysisPeriod to be loaded.
    """
    if analysis_period_str is not None and analysis_period_str != '' \
            and analysis_period_str != 'None':
        return AnalysisPeriod.from_string(analysis_period_str)
