from profpy.web import OracleFlaskApp
from profpy.web import auth

app = OracleFlaskApp(__name__, "Test Application", ["saturn.spriden"])
spriden = app.saturn.spriden


@app.route("/<banner_id>")
@auth.cas_required()
def home(user, attr, banner_id):
    print(app.tables)
    return spriden.as_json(app.db.query(spriden).filter_by(spriden_id=banner_id).first(), as_http_response=True)


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)
