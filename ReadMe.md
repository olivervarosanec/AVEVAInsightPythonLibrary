# AVEVA Insight Python Library
This is a Python library for interacting with the AVEVA Insight API. It allows Tech Support to troubleshoot data issues by providing easy-to-use methods for retrieving and processing data.

# Requirements:
requests
os
json
pandas
numpy
matplotlib
pickle
csv
datetime
Usage
First, you need to initialize an instance of the AvevaInsight class using your access token.

```python
from aveva_insight import AvevaInsight
aveva = AvevaInsight(token='YOUR_ACCESS_TOKEN')
```

# Get Insight Data
To retrieve process values, use the getInsightData method. It requires the tag names, start time, and end time.

```python
df = aveva.getInsightData(tagnames=['Tag1', 'Tag2'], starttime=datetime(2023, 1, 1), endtime=datetime(2023, 1, 31))
Get Expression Data
To retrieve expression data, use the getExpressionData method. It requires an expression, start time, and end time.
```
```python
df = aveva.getExpressionData(expression='Tag1*Tag2', starttime=datetime(2023, 1, 1), endtime=datetime(2023, 1, 31))
```

# Get Tag List
To retrieve a list of available tags, use the getTagList method. Optionally, you can filter the tags by name.

```python
df = aveva.getTagList(tagnames=['Tag1', 'Tag2'])
```

# Further Development
We welcome contributions! If you found a bug or want to suggest an improvement, please open an issue. Pull requests are also welcome.
