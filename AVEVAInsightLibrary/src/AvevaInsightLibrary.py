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
        #self.base_url = 'https://dev.insight.capdev-connect.aveva.com'
        
        self.headers = {
            "Authorization": self.user_token,
            "Content-Type": "application/json"}

        self.process_values_path = '/apis/historian/v2/ProcessValues'
        self.tags_path = '/apis/Historian/V2/Tags'
        self.asset_path = '/apis/cim/v3/entities/query?orderByValue=%40name&includePaths=true&orderByType=Property&orderByDirection=asc'
        self.data_source_path = '/apis/upload/datasource'
        self.get_data_source_path = '/apis/DataSourceServices/DataSources'
        self.get_data_source_token = '/apis/DataSourceServices/GetDataSourceAccessKey'
        self.get_groups_path = 'https://services.connect.aveva.com/uam/v2/groups'
        self.get_users_path = 'https://services.connect.aveva.com/uam/v2/users'
        self.get_role_path = 'https://services.connect.aveva.com/uam/v2/roles?includeAssignable=true&includeSolutionAssignable=true&includePolicyDocument=true&assigneeType=user'
        self.create_user_path = 'https://services.connect.aveva.com/uam/v2/memberships'
        self.create_groups_path = 'https://services.connect.aveva.com/uam/v2/groups'
        self.assign_role_path = 'https://services.connect.aveva.com/uam/v2/roleAssignments'
        self.assign_user_to_group_path = ''
        
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
            return requests.get(url, headers=self.headers, params=params, timeout=500)
        elif method == 'post':
            return requests.post(url, headers=self.headers, json=data, timeout=500)
        else:
            raise ValueError("Invalid method")

    def save_to_file(self, df, filename, filetype="csv"):
        df = df.dropna(subset=['DateTime'])
        #df['DateTime'] = pd.to_datetime(df['DateTime'], format="%Y-%m-%dT%H:%M:%S.%fZ", format='mixed')
        #df['DateTime'] = pd.to_datetime(df['DateTime'], format='mixed')
        df['DateTime'] = df['DateTime'].apply(lambda x: x.strftime("%Y-%m-%d|%H:%M:%S.%f") if pd.notnull(x) else None)

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
                print(f"Failed to retrieve data. Status code: {response.status_code} Reason: {response.reason}")
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

        if 'DateTime' in df.columns:
            df['DateTime'] = pd.to_datetime(df['DateTime'], format='mixed')
        else:
            df['DateTime'] = pd.to_datetime(df['DateTime'])
        return df

    
    def get_data_payload(self, tagname, value): 
        timestamp = datetime.now(pytz.timezone('America/Los_Angeles')).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        data = {
            "data": [
                {
                    "DateTime": timestamp,
                    tagname: value
                }
            ]
        }
        return data
    
    def get_data_payload_from_dataframe(self, dataframe):
        data_list = []

        # Group the dataframe by DateTime and create a dictionary for each group
        grouped = dataframe.groupby('DateTime')
        for name, group in grouped:
            timestamp = name.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            data_dict = {"DateTime": timestamp}
            for _, row in group.iterrows():
                data_dict[row['TagName']] = row['Value']
            data_list.append(data_dict)

        data = {"data": data_list}
        return data


    def get_metadata_payload(self, tagname, Location, DataType, Description, EngUnit):

        data = {
            "metadata": [
            {
            "TagName":tagname,
            "Location": Location,
            "DataType":DataType,
            "Description":Description,
            "EngUnit":EngUnit
        }]
        }
        return data   


    def upload_Tag_Data(self, tagname=None, value=None, dataframe=None):
        if dataframe is not None:
            payload = self.get_data_payload_from_dataframe(dataframe)
        elif tagname is not None and value is not None and dataframe is None:
            payload = self.get_data_payload(tagname, value)
        else:
            raise ValueError("Either dataframe or both tagname and value must be specified")

        api_url = self.base_url + self.data_source_path
        self.headers["Authorization"] = self.datasource_token
        
        df = self.api_call("post", api_url, data=payload)  # Use 'json' parameter instead of 'data'
        
        return df


    def upload_Tag_Metadata(self, tagname, Location, DataType, Description, EngUnit):
        if tagname is None or DataType is None or Description is None or EngUnit is None:
            raise ValueError("tagname and value must be specified")

        payload = self.get_metadata_payload(tagname, Location, DataType, Description, EngUnit)
        print(payload)            

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
    
    def get_datasource_list(self):

        api_url = self.base_url + self.get_data_source_path

        df = self.api_call("get", api_url)

        return df
    
    def get_datasource_token(self, datasourceID):

        if datasourceID is None:
            raise ValueError("datasourceID must be specified")
        
        api_url = self.base_url + self.get_data_source_token + f"?dataSourceId={datasourceID}"

        df = self.api_call("get", api_url)

        return df
    

    def get_asset_list(self, assetName=None, entityDefinition="a2560e20-fe5b-ee15-ed2b-39f79ccab75c"):
        # Verify the input
        if assetName is not None and not isinstance(assetName, (str, list)):
            raise ValueError("assetName must be a string or a list of strings")

        api_url = self.base_url + self.asset_path

        # Construct the query JSON
        query = {
            "$and": [
                {"@name": {"$contains": ""}},  # Placeholder for assetName
                {"@EntityDefinitionID": {"$contains": entityDefinition}}
            ]
        }
        # Update the query with the assetName
        if isinstance(assetName, str):
            query["$and"][0]["@name"]["$contains"] = assetName
        elif isinstance(assetName, list):
            query["$and"] = [{"@name": {"$contains": name}} for name in assetName] + [query["$and"][1]]

        # Call the API
        df = self.api_call("post", api_url, data=query)

            # Initialize an empty list to store the parsed data
        parsed_data = []

        # Iterate over the items in the response
        for item in df["items"]:
            # Extract the required information
            entity_id = item.get('entityId')
            entity_definition_id = item.get('entityDefinitionId')
            name = item.get('name', '')
            # Assume you want the first path if there are multiple paths
            paths = item.get('paths', [])
            path = paths[0].get('path', '') if paths else '' 

            # Append the extracted information as a dictionary to the list
            parsed_data.append({
                'entityId': entity_id,
                'entityDefinitionId': entity_definition_id,
                'path': path,
                'name': name
            })

        # Convert the list of dictionaries to a pandas DataFrame and return
        return pd.DataFrame(parsed_data)

    def get_groups(self, name=None):
        try:
            # Construct the request URL
            url = self.get_groups_path
            if name:
                url += f'?nameContains={name}'
            
            # Make the API request
            response = self._api_request('get', url)

            if response.status_code != 200:
                print(f"Failed to retrieve groups. Status code: {response.status_code} Reason: {response.reason} - {response.text}")
                return None
            else:
                return pd.DataFrame(response.json()['items'])
        except Exception as e:
            print(f"Failed to retrieve groups. Error: {e}")
            return None
        
    def get_users(self, email=None):
        try:
            # Construct the request URL
            url = self.get_users_path
            if email:
                url += f'?emailContains={email}&includeMembershipDetails=true'

            # Make the API request
            response = self._api_request('get', url)

            if response.status_code != 200:
                print(f"Failed to retrieve users. Status code: {response.status_code} Reason: {response.reason} - {response.text}")
                return None
            else:
                return pd.DataFrame(response.json()['items'])
        except Exception as e:
            print(f"Failed to retrieve users. Error: {e}")
            return None
    
    def get_roles(self):
        try:
            response = self._api_request('get', self.get_role_path)

            if response.status_code != 200:
                print(f"Failed to retrieve roles. Status code: {response.status_code} Reason: {response.reason} - {response.text}")
                return None
            else:
                return pd.DataFrame(response.json()['items'])
        except Exception as e:
            print(f"Failed to retrieve roles. Error: {e}")
            return None
        
    def create_user(self, email, connectID):
        try:
            data = {
                "email": email,
                "context": f"account|{connectID}",
            }
            response = self._api_request('post', self.create_user_path, data=data)

            if response.status_code == 409:
                raise Exception(f"User with email {email} already exists.")
                return False
            elif response.status_code == 201:
                print(f"User {email} created successfully")
                return True
            else:
                print(f"Failed to create user. Status code: {response.status_code} Reason: {response.reason} - {response.text}")
                return False
        except Exception as e:
            print(f"Failed to create user. Error: {e}")
            return False
    
    def create_group(self, name, description):
        try:
            data = {
                "name": name,
                "description": description,
            }
            response = self._api_request('post', self.create_groups_path, data=data)

            if response.status_code != 201:
                print(f"Failed to create group. Status code: {response.status_code} Reason: {response.reason} - {response.text}")
                return False
            else:
                print(f"Group {name} created successfully")
                return True
        except Exception as e:
            print(f"Failed to create group. Error: {e}")
            return None
        
    def assign_role_to_group(self, context, groupID, roleID):
        try:
            data = {
                "context": context,
                "group": groupID,
                "role": roleID,
            }
            response = self._api_request('post', self.assign_role_path, data=data)

            if response.status_code != 201:
                print(f"Failed to assign role. Status code: {response.status_code} Reason: {response.reason} - {response.text}")
                return False
            else:
                print(f"Role {roleID} assigned to group {groupID} successfully")
                return True
        except Exception as e:
            print(f"Failed to assign role. Error: {e}")
            return None
    
    def assign_user_to_group(self, groupID, userID):
        try:

            self.assign_user_to_group_path = f"https://services.connect.aveva.com/uam/v2/groups/{groupID}/users"

            data = {
                "id": userID,
            }
            response = self._api_request('post', self.assign_user_to_group_path, data=data)

            if response.status_code != 201:
                print(f"Failed to assign user to group. Status code: {response.status_code} Reason: {response.reason} - {response.text}")
                return False
            else:
                print(f"User {userID} assigned to group {groupID} successfully")
                return True
        except Exception as e:
            print(f"Failed to assign user to group. Error: {e}")
            return None