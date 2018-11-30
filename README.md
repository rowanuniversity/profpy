# profpy
### What is profpy?
The profpy library is a centralized repository for Rowan's various python scripts to use.

### Why use it?
Many of Rowan's python scripts/programs utilize similar or congruent functions and classes that end up getting rewritten or even
copy/pasted wherever needed. Rather than continue this trend of untracked code, profpy allows us to have overhead control over these common functions
and classes. If a program or script needs to use a class or function, it can just import it from profpy rather than rewrite it. This will allow us
to standardize some of our code practices moving forward. 


### Submodules
The profpy library is organized into submodules. For instance, database-related functionality can be access by importing the 
"db" submodule. For example, to import the function that parses together a cx_Oracle connection object one could do this:

```python
from profpy.db import get_connection
connection = get_connection("full_login", "db_password")
```

##### Current Submodules
For in-depth documentation, explore the submodules individually:
- [db](./db)
- [apis](./apis)