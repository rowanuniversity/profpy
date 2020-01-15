import sys 
import argparse
from .cli.run_app import run_app, run_app_argparser
from .cli.flask_init import flask_init, flask_init_prompt, flask_init_argparser

_programs = [
    dict(name="flask-init", description="Initialize a Flask web app with profpy.web tools."),
    dict(name="run-app", description="Run a dockerized web app that you created with one of the profpy init tools."),
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
    

    def run_app(self):
        run_app(run_app_argparser().parse_args(sys.argv[2:]))

    def flask_init(self):
        parser = flask_init_argparser()
        if sys.argv[2:]:
            flask_init(parser.parse_args(sys.argv[2:]))
        else:
            flask_init(parser.parse_args(flask_init_prompt()))


def main():
    Cli()
    