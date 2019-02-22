# ServiceNow Table API 
An API wrapper that optimizes calls to the ServiceNow table API. 

**Note:** this API returns XML. As a result all of this wrapper's methods return xml.etree.ElementTree.Element objects or lists of them. 
Each method has an option for converting these objects to text. 

**[Official ServiceNow API documentation found here](https://docs.servicenow.com/bundle/geneva-servicenow-platform/page/integrate/inbound_rest/concept/c_TableAPI.html)**.
## Basic Usage
This API utilizes user/password credentials for authentication. 
```python
from profpy.apis import ServiceNowTable
api = ServiceNowTable(user="username", password="*****", in_url="this-api-url.com/api/")
```

### Retrieving Data
This class currently only supports endpoints that retrieve data via GET requests. 
```python
from profpy.apis import ServiceNowTable
api = ServiceNowTable(user="username", password="*****", in_url="this-api-url.com/api/")

# returns xml object for matching result
record = api.get_record(table_name="this-table", sys_id="this-record-id")

# returns xml string for matching result 
record = api.get_record(table_name="this-table", sys_id="this-record-id", as_text=True)

# returns list of xml objects for matching results
all_records = api.get_records(table_name="this-table")

# returns a list of xml objects for matching results, with only specified field (other query parameters available in API documentation)
all_records = api.get_records(table_name="this-table", sysparm_fields="field1")
```

# Technical Documentation
## Constructor
### profpy.apis.ServiceNowTable( *user, password, in_url* )
Returns an API handler for the ServiceNow Table API

Parent Class: [profpy.apis.Api](./Api.md)

Parameters: 

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| user  | api user | str          | yes       |    |
| password   | api password    | str | yes       |      |
| in_url | api base url | str | yes |  |

Example:

```python
from profpy.apis import ServiceNowTable
api = ServiceNowTable("user", "password", "url")
```
---
 
## Properties
### authentication_parameters (tup)
The user and password as a tuple; technically the parent class' public_key and private key fields.

---
 
 ## Public Methods
Each method's section will have a link back to ServiceNow's documentation for the corresponding endpoint. You should 
visit these pages for in-depth information on available query parameters. 

### get_record( *table_name, sys_id, as_text=False, \*\*kwargs* )
Returns a record based on table name and sys_id.
 
[Click for further documentation](https://docs.servicenow.com/bundle/geneva-servicenow-platform/page/integrate/inbound_rest/reference/r_TableAPI-GETid.html).
 
Parameters:

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| table_name  | the name of the table that houses the record | str          | yes       |    |
| sys_id      | the system id of the record | str | yes | | |
| as_text     | whether or not to return the result as an XML string | bool | no | False |
| **kwargs    | Keyword args to be used as url query parameters    | **kwargs dict | no       | N/A     |

```python
from profpy.apis import ServiceNowTable
api = ServiceNowTable(user="username", password="*****", in_url="this-api-url.com/api/")

# returns xml object for matching result
record = api.get_record(table_name="this-table", sys_id="this-record-id")

# returns xml text
record = api.get_record(table_name="this-table", sys_id="this-record-id", as_text=True)
```

### get_records( *table_name, as_text=False, \*\*kwargs* )
Returns a list of records based on table name and other specified keyword args.

[Click for further documentation](https://docs.servicenow.com/bundle/geneva-servicenow-platform/page/integrate/inbound_rest/reference/r_TableAPI-GET.html).


Parameters:

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| table_name  | the name of the table that houses the records | str          | yes       |    |
| as_text     | whether or not to return the results as an XML string | bool | no | False |
| **kwargs    | Keyword args to be used as url query parameters    | **kwargs dict | no       | N/A     |

 ```python
from profpy.apis import ServiceNowTable
api = ServiceNowTable(user="username", password="*****", in_url="this-api-url.com/api/")

# returns list of xml objects for matching results
all_records = api.get_records(table_name="this-table")

# returns a list of xml objects for matching results, with only specified field (other query parameters available in API documentation)
all_records = api.get_records(table_name="this-table", sysparm_fields="field1")
```

## Static Methods
### to_xml_text( *in_xml_text* )
Takes in an xml etree object and converts it to text. 

```python
from profpy.apis import ServiceNowTable

xml_str = ServiceNowTable.to_xml_text(some_xml_etree_object)
```