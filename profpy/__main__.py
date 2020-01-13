import sys 
import argparse
from .cli.flask_init import flask_init, flask_init_prompt

_programs = [
    dict(name="flask-init", description="Initialize a Flask web app with profpy.web tools."),
    dict(name="help", description="Get info on profpy CLI tools.")
]


class Cli(object):
    def __init__(self):

        parser = argparse.ArgumentParser(
            description="Profpy CLI tools.",
            usage="profpy <program> [<args>]"
        )

        if not sys.argv[1:]:
            self.help()
        elif sys.argv[1] == "-h":
            self.help()

        parser.add_argument("program", help="The CLI tool to use.", type=str)
        args = parser.parse_args(sys.argv[1:2])

        program = args.program.lower().replace("-", "_")
        if not hasattr(self, program):
            print("Unrecognized program.")
            parser.print_help()
            sys.exit(1)
        getattr(self, program)()

    def help(self):
        print("Profpy CLI tools.")
        print("Usage: profpy <program> [<args>]")
        print("Available programs:")
        for prog in _programs:
            print(f"\t{prog['name']} - {prog['description']}")
        sys.exit(0)
    

    def flask_init(self):
        parser = argparse.ArgumentParser(
            description="Initialize a profpy-flask app."
        )
        parser.add_argument("-n", "--name", required=True, type=str, help="The name of the application.")
        parser.add_argument("-f", "--force-create", action="store_true", help="If the project name already exists in the output directory, delete it before running this tool.")
        parser.add_argument("-p", "--port", required=True, type=int, help="The port that Docker will run this application on.")
        parser.add_argument("-rs", "--role-security", action="store_true", help="Whether or not to configure Spring-like, role-based security.")
        parser.add_argument("-c", "--cas-url", default="https://login.rowan.edu", required=True, type=str, help="The fully-qualified CAS url, (defaults to https://login.rowan.edu)"),
        parser.add_argument("-o", "--output-directory", type=str, help="Optional output directory (defaults to current directory)")
        parser.add_argument("-a", "--asset-management", action="store_true", help="Whether or not to set up integration with Flask-Assets")
        parser.add_argument("-dbu", "--database-user", type=str, required=True, help="The Oracle user that will be the backing database user for this application.")
        parser.add_argument("-dbo", "--database-objects", type=str, nargs="*", help="Any tables/views to allow your app to have access to. Must be fully qualified names (schema.table).")
        parser.add_argument("-rq", "--requirements", type=str, nargs="*", help="Any additional dependencies to have in requirements.txt (profpy is placed in there by default).")
        if sys.argv[2:]:
            flask_init(parser.parse_args(sys.argv[2:]))
        else:
            flask_init(parser.parse_args(flask_init_prompt()))


def main():
    Cli()
    