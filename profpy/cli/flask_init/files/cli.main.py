import os
import logging
from profpy.web import SecureFlaskApp
from profpy.db import get_sql_alchemy_oracle_engine
from flask import render_template
from flask_assets import Environment


engine = get_sql_alchemy_oracle_engine()
tables = {tables}

app = SecureFlaskApp(
    __name__, "{app_name}", engine, tables
)

for config_key in ["app_name", "app_port", "instance", "service", "app_url"]:
    app.config[config_key] = os.getenv(config_key)


# configure gunicorn logging
app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)
app.logger.setLevel(logging.DEBUG)

# configure asset management
assets = Environment(app)


@app.teardown_appcontext
def shutdown_user_session(response_or_error):
    """
    Necessary for database cleanup on session close. If not here, 
    it is possible for the connection to stay open with a bad transaction.
    """
    app.db.rollback()
    return response_or_error


@app.route("/")
@app.route("/home")
@app.route("/index")
@app.secured()
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=8080)
