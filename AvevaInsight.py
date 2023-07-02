import requests
import os
import json
import pandas as pd
import numpy as np
from pandas.tseries.offsets import DateOffset
import urllib.parse
import matplotlib.pyplot as plt
import pickle
from datetime import datetime, timedelta
import csv


class AvevaInsight:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://online.wonderware.eu'
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"}

        self.processValues_path = '/apis/historian/v2/ProcessValues'
        self.tags_path = '/apis/Historian/V2/Tags'
        
    def format_time(self, time):
        time += timedelta(hours=8)
        return time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def convert_datetime(self, dt_str):
        try:
            return pd.to_datetime(dt_str, format="%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return pd.to_datetime(dt_str, format="%Y-%m-%dT%H:%M:%SZ")

    def api_call(self, method, url, params_or_payload, process_func):
        df = pd.DataFrame()
        counter = 0
        while True:
            counter += 1
            if method.lower() == "get":
                response = requests.get(url, headers=self.headers, params=params_or_payload if counter <= 1 else None)
            elif method.lower() == "post":
                response = requests.post(url, headers=self.headers, json=params_or_payload if counter <= 1 else None)
            else:
                raise ValueError("Invalid method")

            if response.status_code == 200:
                df = pd.concat([df, pd.DataFrame(response.json()["value"])])
                df = process_func(df)
                
                if '@odata.nextLink' in response.json():
                    url = response.json()['@odata.nextLink']
                    print(f"next: {counter}")
                    continue
                else:
                    print(f"end: {counter}")
                    break
            else:
                print(f"Failed to retrieve data. Status code: {response.status_code}")
                raise ValueError(f"Error from WEBAPI: {response.content}")

        return df
    
    def getInsightData(self, tagnames, starttime, endtime, RetrievalMode="Delta"):
        # Verify the input
        if not isinstance(starttime, datetime):
            raise ValueError("starttime must be a datetime object")
        if not isinstance(endtime, datetime):
            raise ValueError("endtime must be a datetime object")
        if not isinstance(tagnames, (str, list)):
            raise ValueError("tagnames must be a string or a list of strings")

        api_url = self.base_url + self.processValues_path
        starttime, endtime = self.format_time(starttime), self.format_time(endtime)

        if isinstance(tagnames, str):
            tag_filter = f"endswith(FQN, '{tagnames}')"
        else:
            tag_filter = " or ".join([f"endswith(FQN, '{tagname}')" for tagname in tagnames])

        params = {
            "TagFilter": tag_filter,
            "RetrievalMode": RetrievalMode,
            "$filter": f"DateTime ge {starttime} and DateTime le {endtime}"
        }
        df = self.api_call("get", api_url, params, lambda df: df.sort_values('DateTime', ascending=True))

        return df

    def getExpressionData(self, expression, starttime, endtime, RetrievalMode="Delta"):
        # Verify the input
        if not isinstance(starttime, datetime):
            raise ValueError("starttime must be a datetime object")
        if not isinstance(endtime, datetime):
            raise ValueError("endtime must be a datetime object")
        if not isinstance(expression, str):
            raise ValueError("expression must be a string")

        api_url = self.base_url + self.processValues_path
        starttime, endtime = self.format_time(starttime), self.format_time(endtime)

        payload = {
            "fqn": [],
            "startDateTime": starttime,
            "endDateTime": endtime,
            "RetrievalMode": RetrievalMode,
            "select": "DateTime,FQN,OpcQuality,Value,Unit,InterpolationType",
            "expression": expression
        }
        df = self.api_call("post", api_url, payload, lambda df: df.sort_values('DateTime', ascending=True))

        return df

    def getTagList(self, tagnames=None):
        # Verify the input
        if tagnames is not None and not isinstance(tagnames, (str, list)):
            raise ValueError("tagnames must be a string or a list of strings")

        api_url = self.base_url + self.tags_path

        params = ""

        if isinstance(tagnames, str):
            tag_filter = f"startswith(FQN, '{tagnames}')"
            params = {"$filter": tag_filter}
        elif isinstance(tagnames, list):
            tag_filter = " or ".join([f"startswith(FQN, '{tagname}')" for tagname in tagnames])
            params = {"$filter": tag_filter}
        else:
            tag_filter = ""

        df = self.api_call("get", api_url, params, lambda df: df)

        return df