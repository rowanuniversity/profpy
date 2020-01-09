from profpy.web import SecureFlaskApp
from profpy.db import get_sql_alchemy_oracle_engine
{asset_import}

engine = get_sql_alchemy_oracle_engine()
tables = {tables}

app = SecureFlaskApp(
    __name__, "{app_name}", engine, tables
)

{asset_config}

@app.route("/index")
def index():
    return "<h1>Hello, world</h1>"


if __name__ == "__main__":
    app.run(debug=True, port=8080)