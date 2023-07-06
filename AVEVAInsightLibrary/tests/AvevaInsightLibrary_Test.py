import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
aveva_insight_library_path = os.path.join(current_dir, '..')
sys.path.append(aveva_insight_library_path)
from src.AvevaInsightLibrary import Aveva_Insight
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()

@pytest.fixture
def insight():
    def _insight_with_token(token):
        return Aveva_Insight(token)

    return _insight_with_token

def assign_bearer_token():
    return os.getenv('BEARER_TOKEN')

def test_format_time(insight):
    token = assign_bearer_token()
    insight_instance = insight(token)
    test_datetime = datetime(2022, 1, 1, 0, 0)

    result = insight_instance.format_time(test_datetime)

    assert result == "2022-01-01T08:00:00Z", "Format time method is not working as expected"

def test_convert_datetime(insight):
    token = assign_bearer_token()
    insight_instance = insight(token)
    datetime_str = "2022-01-01T08:00:00.000Z"

    result = insight_instance.convert_datetime(datetime_str)
    
    assert isinstance(result, pd.Timestamp), "Convert datetime method is not returning pandas Timestamp"

def test_get_Insight_Data(insight):
    token = assign_bearer_token()
    insight_instance = insight(token)
    tagnames = 'CH-Vevey.EUR.Switzerland.Vevey.UTI01.BH01.PKBOI01.SteamFlow'
    starttime = datetime(2023, 6, 1, 0, 0)
    endtime = datetime(2023, 6, 2, 0, 0)
    
    result = insight_instance.get_Insight_Data(tagnames, starttime, endtime, RetrievalMode="Full")

    assert result.shape[0] > 0, "getInsightData method is not returning any data"
    assert result.shape[1] == 6, "getInsightData method is not returning the expected number of columns"

    expected_columns = ['FQN', 'DateTime', 'OpcQuality', 'Value', 'Text', 'Unit']
    for col in expected_columns:
        assert col in result.columns, f"getInsightData method is not returning the expected column: {col}"
  
def test_get_Expression_Data(insight):
    token = assign_bearer_token()
    insight_instance = insight(token)
    tagnames = 'AVERAGE([CH-Vevey.EUR.Switzerland.Vevey.UTI01.BH01.PKBOI01.SteamEnthalpy], 1 Month)'
    starttime = datetime(2023, 6, 1, 0, 0)
    endtime = datetime(2023, 6, 2, 0, 0)
    
    result = insight_instance.get_Expression_Data(tagnames, starttime, endtime)

    assert result.shape[0] > 0, "getInsightData method is not returning any data"
    assert result.shape[1] == 6, "getInsightData method is not returning the expected number of columns"

    expected_columns = ['FQN', 'DateTime', 'OpcQuality', 'Value', 'Unit', 'InterpolationType']
    for col in expected_columns:
        assert col in result.columns, f"getInsightData method is not returning the expected column: {col}"

def test_get_Tag_List(insight):
    token = assign_bearer_token()
    insight_instance = insight(token)

    result = insight_instance.get_Tag_List()

    assert result.shape[0] > 0, "getInsightData method is not returning any data"
    assert result.shape[1] > 6, "getInsightData method is not returning the expected number of columns"
