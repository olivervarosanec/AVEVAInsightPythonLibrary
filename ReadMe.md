# AVEVA Insight Python Library
This is a Python module designed to facilitate communication with the AVEVA Insight API. 
It offers users the convenience of accessing data through user-friendly methods, transforming it into pandas dataframes for ease of processing and manipulation.

Python Version: > 3.8

```python
from aveva_insight import Aveva_Insight
aveva = Aveva_Insight(token='YOUR_ACCESS_TOKEN')
```

# Get Insight Data
To retrieve process values, use the get_Insight_Data method. It requires the tag names, start time, and end time.

```python
df = aveva.get_Insight_Data(tagnames=['Tag1', 'Tag2'], starttime=datetime(2023, 1, 1), endtime=datetime(2023, 1, 31), RetrievalMode="Delta")
```

# Get Expression Data
To retrieve expression data, use the get_Expression_Data method. It requires an expression, start time, and end time.

```python
df = aveva.get_Expression_Data(expression='Tag1*Tag2', starttime=datetime(2023, 1, 1), endtime=datetime(2023, 1, 31), RetrievalMode="Delta")
```

# Get Tag List
To retrieve a list of available tags, use the get_Tag_List method. Optionally, you can filter the tags by name.

```python
df = aveva.get_Tag_List(tagnames=['Tag1', 'Tag2'])
```

# Further Development
We welcome contributions! If you found a bug or want to suggest an improvement, please open an issue. Pull requests are also welcome.
