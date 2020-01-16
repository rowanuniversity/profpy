import os
import logging
from profpy.web import SecureFlaskApp
from profpy.db import get_sql_alchemy_oracle_engine
from flask import render_template
{asset_import}

engine = get_sql_alchemy_oracle_engine()
tables = {tables}

app = SecureFlaskApp(
    __name__, "{app_name}", engine, tables
)
app.config["app_name"] = os.getenv("app_name")

# configure gunicorn logging
app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)
app.logger.setLevel(logging.DEBUG)

{asset_config}

@app.teardown_appcontext
def shutdown_user_session(response_or_error):
    """
    Necessary for database cleanup on session close. If not here, 
    it is possible for the connection to stay open with a bad transaction.
    """
    try:
        if response_or_error is None:
            app.db.commit()
    finally:
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