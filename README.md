# profpy
### What is profpy?
The profpy library is a centralized repository for Rowan's various python scripts to use.

Looking for ```fauxrm``` docs? Click [here](./profpy/db/fauxrm/).

### Why use it?
Many of Rowan's python scripts/programs utilize similar or congruent functions and classes that end up getting rewritten or even
copy/pasted wherever needed. Rather than continue this trend of untracked code, profpy allows us to have overhead control over these common functions
and classes. If a program or script needs to use a class or function, it can just import it from profpy rather than rewrite it. This will allow us
to standardize some of our code practices moving forward. 

### Installation
```bash
pip3 install profpy
```

### Submodules
The profpy library is organized into submodules. For instance, database-related functionality can be accessed by importing the 
"db" submodule. For example, to import the function that parses together a cx_Oracle connection object one could do this:

```python
from profpy.db import get_connection

if __name__ == "__main__":
    connection = get_connection("full_login", "db_password")
    cursor = connection.cursor()
    # do stuff
```
or
```python
from profpy.db import with_oracle_connection

@with_oracle_connection()
def main(connection):
    cursor = connection.cursor()
    # do stuff

if __name__ == "__main__":
    main()
```

<i>Note: "full_login" and "db_password" are the defaults for both methods</i>

#### Exception Handling
The profpy database functions leverage Oracle exceptions, so any custom exception handling will likely involve 
cx_Oracle errors.
```python
from cx_Oracle import IntegrityError, DatabaseError
from profpy.db import with_oracle_connection

sql = "select * from test.table where test_column=:param1"
params = dict(param1="value")

@with_oracle_connection()
def main(connection):
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
    except DatabaseError:
        # do some stuff
        ...
    except IntegrityError:
        # do some stuff
        ...
    else:
        connection.commit()
    finally:
        cursor.close()
```
Note: the ```with_oracle_connection``` function handles the closing of the connection object, and does a rollback.


#### Auto-commit
You can also use the "auto_commit" flag in the decorator to streamline your code.
```python
from profpy.db import with_oracle_connection

@with_oracle_connection(auto_commit=True)
def main(connection):
    ...
```

### Dependencies
Python 3.6.7 or above

##### Current Submodules
For in-depth documentation, explore the submodules individually:
- [db](./profpy/db)
    * [fauxrm](./profpy/db/fauxrm)
- [apis](./profpy/apis)
- [auth](./profpy/auth)

If you are looking to make a flask application with fauxrm, go [here](./profpy/db/fauxrm/documentation/flask.md). 