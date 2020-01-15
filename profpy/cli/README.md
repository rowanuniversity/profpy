# profpy CLI

As of version 3.0, profpy installation now includes a suite of command line tools.
These tools are placed in the user's path upon installation, allowing for them to
be called directly on the commnand line with the entrypoint ```profpy```

Get a list of available tools:

```shell script
# either one works
profpy -h
profpy help
```

## Web Development

### flask-init

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

There are two ways of utilizing this tool. The first way is to enter information via prompts. You can
access this feature by entering no arguments:

```shell script
profpy flask-init
```

The other way is to directly input values via flag parameters:

```shell script
profpy flask-init [-n, --name]  [-p, --port] [-c, --cas-url] [-o, --output-directory] [-dbu, --database-user] [-dbo, --database-objects (list)] [-rq, --requirements (list)] [-rs, --role-security (boolean flag)] [-f, --force-create (boolean flag)] [-a, --asset-management (boolean flag)]
```

For a more detailed explanation of these arguments:

```shell script
profpy flask-init -h
```

### run-app

Run a containerized web application that you created via a ```profpy``` init tool. The ```profpy``` init tools
set up ```Docker``` files in a way that allow you to quickly run web applications against different database instances.

To run your application (for the example, we'll call it ```webapp```):

```shell script
cd webapp
profpy run-app
```

What did that do? The ```run-app``` command sets up a running container for your web application using ```meinheld``` and
```gunicorn```. By default, this command runs against ```dev``` (PPRD). When in ```dev``` mode, the container is
interactive. This means that you can view any code changes to you app by simply refreshing your web browser
(rather than needing to restart the container). When running in ```test``` (FORTNGHT) or ```prod``` (PROD) mode, the container
is not interactive, and is run in detached mode.

Here are some basic examples:

```shell script
# create some app, most prompts/parameters skipped for clarity
profpy flask-init -n webapp
cd webapp

# set the correct database password in .env (alternatively, this can be done in a text editor)
sed -i \"\" 's/db_password=/db_password=MYPASSWORD/g' .env

# run the app in dev mode
profpy run-app

# run the app in dev mode, with detached container
profpy run-app -d

# run the app in test mode
profpy run-app test

# run the app in prod mode
profpy run-app prod

# prompt docker to "force recreate the image"
profpy run-app --force-recreate
```

You can also run an app that is in a different directory using the ```-ap, --app-path``` flag:

```shell script
profpy run-app -ap /path/to/webapp
profpy run-app test -ap /path/to/webapp
```

### stop-app

Stop a running, detached container that you started with ```run-app```.

```shell script
# start the app
profpy run-app prod

# stop the app
profpy stop-app
```

When outside of the app:

```shell script
# start the app
profpy run-app prod -ap /path/to/webapp

# stop the app
profpy stop-app -ap /path/to/webapp
```

## Database Tools
