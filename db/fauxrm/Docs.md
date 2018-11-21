# profpy.db.fauxrm - Technical Documentation

### profpy.db.fauxrm.Database ( *login_var="full_login", password_var="db_password"* )
Returns a Database object which acts as a window into the database available to the specified credentials. Database
objects have their own internal connection and cursor objects that get appropriately opened and closed if used 
within a "with-block". If not, Database objects must be explicitly closed.

Parameters:

| Name         | Description                                           | Type | Required | Default       |
|--------------|-------------------------------------------------------|------|----------|---------------|
| login_var    | environment variable containing database login string | str  | no       | "full_login"  |
| password_var | environment variable containing database password     | str  | no       | "db_password" |

Example:

```python
from profpy.db import fauxrm

# with context management
with fauxrm.Database() as database:
    pass
    
# without context management
database = fauxrm.Database()
database.close()
```


#### Methods
#### model ( *owner, object_name* )
Returns either a Table or View handler object, depending on which type the object specified is. Table and View objects
are children of the Data class, and can be used to retrieve/modify data. For more information on the Table and View 
class' methods, see their documentation below.

Parameters:

| Name        | Description                                 | Type | Required |
|-------------|---------------------------------------------|------|----------|
| owner       | schema name where the table/view is located | str  | yes      |
| object_name | name of the table/view                      | str  | yes      |

Example:
```python
from profpy.db import fauxrm
with fauxrm.Database() as database:
    spvname = database.model("rowan", "spvname")
```