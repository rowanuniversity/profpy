# ServiceNow Table API 
An API wrapper that optimizes calls to the ServiceNow table API. 

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

# returns json for matching result
record = api.get_record(table_name="this-table", record_id="this-record-id")

# returns list of json objects for matching results
all_records = api.get_records(table_name="this-table")

# returns json object based on different id field
record = api.get_record(table_name="this-table", record_id="this-record-id", custom_id_field="alternative-id-field")
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

### get_record( *table_name, record_id, custom_id_field, \*\*kwargs* )
Returns a record based on table name and sys_id.
 
[Click for further documentation](https://docs.servicenow.com/bundle/geneva-servicenow-platform/page/integrate/inbound_rest/reference/r_TableAPI-GETid.html).
 
Parameters:

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| table_name  | the name of the table that houses the record | str          | yes       |    |
| record_id      | the id of the record | str | yes | | |
| custom_id_field     | an alternative id field to use for the search | str | no | None |
| **kwargs    | Keyword args to be used as url query parameters    | **kwargs dict | no       | N/A     |

```python
from profpy.apis import ServiceNowTable
api = ServiceNowTable(user="username", password="*****", in_url="this-api-url.com/api/")

# returns json for matching result
record = api.get_record(table_name="this-table", record_id="this-record-id")

# returns record based on different id field
record = api.get_record(table_name="this-table", record_id="this-record-id", custom_id_field="alternative-id-field")
```

### get_records( *table_name, \*\*kwargs* )
Returns a list of records based on table name and other specified keyword args.

[Click for further documentation](https://docs.servicenow.com/bundle/geneva-servicenow-platform/page/integrate/inbound_rest/reference/r_TableAPI-GET.html).


Parameters:

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| table_name  | the name of the table that houses the records | str          | yes       |    |
| **kwargs    | Keyword args to be used as url query parameters    | **kwargs dict | no       | N/A     |

 ```python
from profpy.apis import ServiceNowTable
api = ServiceNowTable(user="username", password="*****", in_url="this-api-url.com/api/")

# returns list of json objects for matching results
all_records = api.get_records(table_name="this-table")

# returns a list of json objects for matching results, with only specified field (other query parameters available in API documentation)
all_records = api.get_records(table_name="this-table", sysparm_fields="field1")

# alternatively, when dealing with larger tables that may require API paging, use the "load_table" function instead
all_records = api.load_table(table_name="this-table", limit=100, any_other_query_params="some_value")
```