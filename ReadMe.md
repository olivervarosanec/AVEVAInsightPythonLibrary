# 🚀 AVEVA Insight Python Library

📊 A powerful Python module for seamless interaction with the AVEVA Insight API. 
Effortlessly retrieve and manipulate data using pandas dataframes!

## 🛠️ Requirements

- Python 3.8+
- Required packages: `requests`, `pandas`, `pytz`

## 🚀 Quick Start

Initialize the client:

```python
from aveva_insight import Aveva_Insight

aveva = Aveva_Insight(user_token='YOUR_USER_TOKEN', datasource_token='YOUR_DATASOURCE_TOKEN')
```

## 🔧 Key Features

### 📈 Get Insight Data

Retrieve process values with ease:

```python
df = aveva.get_Insight_Data(
    tagnames=['Tag1', 'Tag2'],
    starttime=datetime(2023, 1, 1),
    endtime=datetime(2023, 1, 31),
    RetrievalMode="Delta",
    Resolution="1h",
    InterpolationType="Linear"
)
```

### 🧮 Get Expression Data

Fetch calculated expression data:

```python
df = aveva.get_Expression_Data(
    expression='Tag1*Tag2',
    starttime=datetime(2023, 1, 1),
    endtime=datetime(2023, 1, 31),
    RetrievalMode="Delta",
    Resolution="1h"
)
```

### 📤 Upload Tag Data

Send live data with current timestamp:

```python
df = aveva.upload_Tag_Data(tagname= "Tag1", value = 1)
```
To Upload history values as Pandas Dataframe

```python
df = aveva.upload_Tag_Data(dataframe= pandasDataframe)


Or upload multiple tags using a dataframe:

```python
df = pd.DataFrame({
    'DateTime': [datetime.now(), datetime.now()],
    'TagName': ['Tag1', 'Tag2'],
    'Value': [1, 2]
})
result = aveva.upload_Tag_Data(dataframe=df)
```

### 📋 Get Tag List

Retrieve available tags, with optional filtering:

```python
df = aveva.get_Tag_List(tagnames=['Tag1', 'Tag2'])
```

### 🏭 Get Asset List

Fetch asset information:

```python
df = aveva.get_asset_list(assetName="Pump", entityDefinition="YOUR_ENTITY_DEFINITION_ID")
```

### 📊 Data Source Management

List data sources and get tokens:

```python
datasources = aveva.get_datasource_list()
token = aveva.get_datasource_token(datasourceID="YOUR_DATASOURCE_ID")
```

### 👥 User and Group Management

Manage users, groups, and roles:

```python
users = aveva.get_users(email="user@example.com")
groups = aveva.get_groups(name="Engineers")
roles = aveva.get_roles()

aveva.create_user(email="newuser@example.com", connectID="CONNECT_ID")
aveva.create_group(name="New Group", description="Description")
aveva.assign_role_to_group(context="CONTEXT", groupID="GROUP_ID", roleID="ROLE_ID")
aveva.assign_user_to_group(groupID="GROUP_ID", userID="USER_ID")
```

## 📝 Note

This library uses the AVEVA Insight API. Ensure you have the necessary permissions and valid tokens to access the API.

## 🤝 Contributing

We welcome contributions! Found a bug or have a feature request? Open an issue or submit a pull request.

## ⚠️ Disclaimer
This is not an official AVEVA product. Use at your own risk.

