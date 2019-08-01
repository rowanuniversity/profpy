### OracleFlaskApp(*context, name, in_tables, login, password*)
<i>Extension of the Flask application class. Caller provides the app location context (should almost always be ```__name__```), 
and a list of schema-qualified table/view names.</i>

<b>Constructor Parameters:</b>

| Name         | Description                                             | Type | Required | Default |
|--------------|---------------------------------------------------------|------|----------| ------- |
| context | Flask app location context | str | yes | |
| name | Descriptive name of the application | str | yes ||
| in_tables | A list of schema-qualified table/view names for the app to have access to | list | no | [] |
| login    | login connection string | str  | no      | full_login environment var |
| password | database password       | str  | no      | db_password environment var|


```python
from profpy.web import OracleFlaskApp

app = OracleFlaskApp(__name__, "My App", ["schema.table1", "schema.table2"], "login", "password")
```

#### Non-Model Properties
##### db
<i>A Sql-Alchemy scoped session that can be used to execute SQL</i>
```python
app.db.execute("select * from some_table")
```

##### application_name
<i>The descriptive name of the application</i>
```python
print(app.application_name)
```

##### Parent Properties set by constructor
| Property | Value |
|----------|-------|
|secret_key|str(uuid())|
|url_map.strict_slashes | False|
|config["JSONIFY_PRETTYPRINT_REGULAR"]|True|


#### Methods
##### healthcheck()
<i>Simple ping to the database to see if the connection is up. Returns a jsonified Flask response.</i>
```python
app.healthcheck()
```

##### teardown()
<i>Closes the Sql-Alchemy session</i>
```python
app.teardown()
```