## 25Live API
An wrapper to optimize calls to the 25Live API. 25Live data includes information on spaces and reservations on campus.

### Basic Usage
This API's core functionality currently does not require authentication.
```python
from profpy.apis import TwentyFiveLive

api = TwentyFiveLive()

# grab space json
spaces = api.get_spaces()

# grab reservation json
reservations = api.get_reservations()

# grab organization json
organizations = api.get_organizations()

# grab organization type json
org_types = api.get_organization_types()
```

---

##  Constructor
### profpy.apis.TwentyFiveLive(&nbsp;)
Returns an api handler for the 25Live api for Rowan

Parameters: *None*

Example:
```python
from profpy.apis import TwentyFiveLive
api = TwentyFiveLive()
```

## Properties
No public properties defined in this class, see [parent class documentation](./Api.md) for parent's public properties.

## Methods
### get_organizations( *as_xml_text=False, \*\*kwargs* ):
Returns organizations as json from 25Live.

Parameters:

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| as_xml_text | if True, returns original xml from api as a string | bool          | no       | False   |
| **kwargs    | Keyword args to be used as url query parameters    | **kwargs dict | no       | N/A     |

Accepted query parameters: organization_id

Example
```python
from profpy.apis import TwentyFiveLive
api = TwentyFiveLive()

# get all organizations
orgs = api.get_organizations()

# get organization with id of 2
org = api.get_organizations(organization_id=2)
```

### get_organization_types( *as_xml_text=False, \*\*kwargs* ):
Returns organization types as json from 25Live.

Parameters:

| Name        | Description                                        | Type          | Required | Default |
|-------------|----------------------------------------------------|---------------|----------|---------|
| as_xml_text | if True, returns original xml from api as a string | bool          | no       | False   |
| **kwargs    | Keyword args to be used as url query parameters    | **kwargs dict | no       | N/A     |

Accepted query parameters: organization_id

Example
```python
from profpy.apis import TwentyFiveLive
api = TwentyFiveLive()

# get all organizations
orgs = api.get_organization_types()

# get organization type with id of 2
org = api.get_organization_types(type_id=2)
```



