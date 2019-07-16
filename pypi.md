# profpy
### What is profpy?
The profpy library is a centralized repository for Rowan's various python scripts to use.

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
The profpy library is organized into submodules. For instance, database-related functionality can be access by importing the 
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

### Dependencies
- Python 3.6.7 or above
- Oracle Instant Client

