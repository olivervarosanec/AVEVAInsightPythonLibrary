import requests
import pandas as pd
from pandas.tseries.offsets import DateOffset
from datetime import datetime, timedelta
import json
import pytz
 

class Aveva_Insight:
    def __init__(self, user_token=None, datasource_token=None):
        self.user_token = user_token
        self.datasource_token = datasource_token

        self.base_url = 'https://online.wonderware.eu'
        self.headers = {
            "Authorization": self.user_token,
            "Content-Type": "application/json"}

        self.process_values_path = '/apis/historian/v2/ProcessValues'
        self.tags_path = '/apis/Historian/V2/Tags'
        self.data_source_path = '/apis/upload/datasource'
        
    def format_time(self, time):
        #time += timedelta(hours=8)
        return time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def convert_datetime(self, dt_str):
        try:
            return pd.to_datetime(dt_str, format="%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            try:
                return pd.to_datetime(dt_str, format="%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                raise ValueError("Invalid datetime format")

    def _api_request(self, method, url, data=None, params=None):
        if method == 'get':
            return requests.get(url, headers=self.headers, params=params)
        elif method == 'post':
            return requests.post(url, headers=self.headers, json=data)
        else:
            raise ValueError("Invalid method")

    def save_to_file(self, df, filename, filetype="csv"):
        df = df.dropna(subset=['DateTime'])
        #df['DateTime'] = pd.to_datetime(df['DateTime'], format="%Y-%m-%dT%H:%M:%S.%fZ", format='mixed')
        df['DateTime'] = pd.to_datetime(df['DateTime'], format='mixed')
        #df['DateTime'] = df['DateTime'].apply(lambda x: x.strftime("%Y-%m-%d|%H:%M:%S.%f") if pd.notnull(x) else None)

        if filetype.lower() == "csv":
            # create the CSV file with the specified format
            with open(filename + '.csv', 'w') as f:
                f.write("ASSCII\n|\nAdmin|UTC|UTC|DEFAULT|DEFAULT\n")
                for index, row in df.iterrows():
                    last_string = row['FQN'].split('.')[-1]
                    f.write(f"{last_string}|0|{row['DateTime']}|1|{row['Value']}|{row['OpcQuality']}\n")
        elif filetype.lower() == "json":
            # export the DataFrame to a JSON file
            df.to_json(filename + '.json', orient="records")
        else:
            raise ValueError("Invalid filetype. Use 'json' or 'csv'.")

    def api_call(self, method, url, params=None, data=None, process_func=None):
        df = pd.DataFrame()
        counter = 0
        while True:
            counter += 1
            response = self._api_request(method, url, params=params if counter == 1 else None, data=data)
            
            if response.status_code not in [200, 202]:
                print(f"Failed to retrieve data. Status code: {response.status_code}")
                raise ValueError(f"Error from WEBAPI: {response.content}")

            response_data = response.json()
            if "value" in response_data:
                df = pd.concat([df, pd.DataFrame(response_data["value"])])
            else:
            # Just return the root object if "value" does not exist
                df = response_data


            if len(df) > 0 and process_func is not None:
                df = process_func(df)

            if '@odata.nextLink' in response.json():
                url = response.json()['@odata.nextLink']
                print(f"next: {counter}")
            else:
                break

        return df

    def get_Insight_Data(self, tagnames, starttime=None, endtime=None, relative_days=None, RetrievalMode=None, Resolution=None, InterpolationType=None):
        # Verify the input
        if relative_days is not None:
            if not isinstance(relative_days, int):
                raise ValueError("relative_days must be an integer")
            endtime = datetime.now()
            starttime = endtime - timedelta(days=relative_days)
        else:
            if not isinstance(starttime, datetime):
                raise ValueError("starttime must be a datetime object")
            if not isinstance(endtime, datetime):
                raise ValueError("endtime must be a datetime object")

        if not isinstance(tagnames, (str, list)):
            raise ValueError("tagnames must be a string or a list of strings")

        api_url = self.base_url + self.process_values_path
        starttime, endtime = self.format_time(starttime), self.format_time(endtime)

        if isinstance(tagnames, str):
            tag_filter = f"endswith(FQN, '{tagnames}')"
        else:
            tag_filter = " or ".join([f"endswith(FQN, '{tagname}')" for tagname in tagnames])

        params = {
            "TagFilter": tag_filter,
            "$filter": f"DateTime ge {starttime} and DateTime le {endtime}"
        }
        if Resolution is not None:
            params["Resolution"] = Resolution
        if RetrievalMode is not None:
            params["RetrievalMode"] = RetrievalMode
        if InterpolationType is not None:
            params["InterpolationType"] = InterpolationType

        df = self.api_call("get", api_url, params=params, process_func=lambda df: df.sort_values('DateTime', ascending=True))

        df['DateTime'] = pd.to_datetime(df['DateTime'], format='mixed')
        return df

    def get_Expression_Data(self, expression, starttime=None, endtime=None, relative_days=None, RetrievalMode=None,  Resolution=None):
        
        # Verify the input
        if relative_days is not None:
            if not isinstance(relative_days, int):
                raise ValueError("relative_days must be an integer")
            endtime = datetime.now()
            starttime = endtime - timedelta(days=relative_days)
        else:
            if not isinstance(starttime, datetime):
                raise ValueError("starttime must be a datetime object")
            if not isinstance(endtime, datetime):
                raise ValueError("endtime must be a datetime object")
        if not isinstance(expression, str):
            raise ValueError("expression must be a string")

        api_url = self.base_url + self.process_values_path
        starttime, endtime = self.format_time(starttime), self.format_time(endtime)

        payload = {
            "fqn": [],
            "startDateTime": starttime,
            "endDateTime": endtime,
            "select": "DateTime,FQN,OpcQuality,Value,Unit,InterpolationType",
            "expression": expression
        }

        if Resolution is not None:
            payload["Resolution"] = Resolution
        if RetrievalMode is not None:
            payload["RetrievalMode"] = RetrievalMode

        #print(payload)

        df = self.api_call("post", api_url, data=payload, process_func=lambda df: df.sort_values('DateTime', ascending=True))

        df['DateTime'] = pd.to_datetime(df['DateTime'], format='mixed')
        return df

    
    def get_data_payload(self, tagname, value):

        timestamp = datetime.now(pytz.timezone('America/Los_Angeles')).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        data = {
            "data":[
            {
                "DateTime":timestamp,
                tagname:value
            }
        ]
        }

        return data   


    def upload_Tag_Data(self, tagname, value):
        if tagname is None or value is None:
            raise ValueError("tagname and value must be specified")

        payload = self.get_data_payload(tagname, value)
        #print(payload)            

        api_url = self.base_url + self.data_source_path
        self.headers["Authorization"] = self.datasource_token
        
        df = self.api_call("post", api_url, data=payload)
        
        return df


    def get_Tag_List(self, tagnames=None):
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