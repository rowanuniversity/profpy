# profpy CLI

As of version 3.0, profpy installation now includes a suite of command line tools.
These tools are placed in the user's path upon installation, allowing for them to
be called directly on the commnand line with the entrypoint ```profpy```

## flask-init

Creates a Flask application directory structure, complete with Rowan design standards
and ```docker-compose``` configuration. The created app will include the following:

- an ```app``` subdirectory containing all Flask code, utilizing the profpy.web.SecureFlaskApp
class for ```CAS``` and role-based security. Included here are the following directories: ```templates/```,
```static/```, ```utils/```

- a ```dba``` subdirectory containing a database schema setup script

- containerization via ```Docker```

- appropriate ```SAMPLE.env``` and ```.env``` files

- a ```.gitignore``` file

- a barebones ```README.md``` file

### Usage

There are two ways of utilizing this tool. The first way is to enter information via prompts. You can
access this feature by entering no arguments:

```shell script
profpy flask-init
```

The other way is to directly input values via flag parameters:

```shell script
profpy flask-init [-n, --name]  [-p, --port] [-c, --cas-url] [-o, --output-directory] [-dbu, --database-user] [-dbo, --database-objects (list)] [-rq, --requirements (list)] [-rs, --role-security (boolean flag)] [-f, --force-create (boolean flag)] [-a, --asset-management (boolean flag)]
```

