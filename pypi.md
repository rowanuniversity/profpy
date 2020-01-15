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

### CLI

For details on the ```profpy``` command line interface, [read the docs](https://github.com/rowanuniversity/profpy/tree/master/profpy/cli).

### Submodules
The profpy library is organized into submodules: ```db```, ```web```, and ```apis```. The ```db``` submodule makes accessing
Oracle databases with cx_Oracle and or Sql-Alchemy simpler. The ```apis``` submodule 
contains wrapper-classes for some commonly used web APIs. The ```web``` submodule contains code for making easy,
database-backed Flask apps, configured with CAS and role-based security.

All three of these submodules can be used to cut back on duplicated code, as well as make the development process much less
time consuming.  


For in-depth documentation, explore the submodules individually:
- [db](https://github.com/rowanuniversity/profpy/tree/master/profpy/db)
- [apis](https://github.com/rowanuniversity/profpy/tree/master/profpy/apis)
- [web](https://github.com/rowanuniversity/profpy/tree/master/profpy/web)


### Dependencies
- Python 3.6.7 or above
- Oracle Instant Client

