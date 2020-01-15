"""
__main__.py

Entrypoint for the profpy CLI tool suite. This gets installed on the user's path once profpy is installed. 
Users can call tools on the command line like so:
    profpy <tool> <args>
"""
import sys 
import argparse
from .cli.run_app import run_app, run_app_argparser
from .cli.flask_init import flask_init, flask_init_prompt, flask_init_argparser
from .cli.stop_app import stop_app, stop_app_argparser


# valid programs
_programs = [
    dict(name="flask-init", description="Initialize a Flask web app with profpy.web tools."),
    dict(name="run-app", description="Run a dockerized web app that you created with one of the profpy init tools."),
    dict(name="stop-app", description="Stop a dockerized web app that you created with one of the profpy init tools."),
    dict(name="help", description="Get info on profpy CLI tools.")
]


class Cli(object):
    """
    This class handles the calling of profpy CLI tools.
    """
    def __init__(self):
        """
        Constructor. Evaluates the input.
        """

        # the base argparser that only looks for a program/tool to pivot to
        parser = argparse.ArgumentParser(
            description="Profpy CLI tools.",
            usage="profpy <program> [<args>]"
        )

        # user provided no args, default to the help text
        if not sys.argv[1:]:
            self.help()
        elif sys.argv[1] == "-h":
            self.help()

        # only use this argparser to evaluate the first positional argument
        parser.add_argument("program", help="The CLI tool to use.", type=str)
        args = parser.parse_args(sys.argv[1:2])

        # store any other args (post tool name)
        self.__prog_args = sys.argv[2:]
        program = args.program.lower().replace("-", "_")

        # no tool for the given arg
        if not hasattr(self, program):
            print("Unrecognized program.")
            parser.print_help()
            sys.exit(1)
        
        # call the appropriate method for the tool specified by the user
        getattr(self, program)()


    def help(self):
        """
        A useful help screen that displays usage info and a list of available programs.
        """
        print("Profpy CLI tools.")
        print("Usage: profpy <program> [<args>]")
        print("Available programs:")
        for prog in _programs:
            print(f"\t{prog['name']} - {prog['description']}")
        sys.exit(0)
    

    def run_app(self):
        """
        Runs a web application using docker. 
        This will only work with apps that were initialized by a profpy init tool, i.e. "profpy flask-init".
        """
        run_app(run_app_argparser().parse_args(self.__prog_args))


    def stop_app(self):
        """
        Stops a dockerized web application that was initialized via profpy CLI init tools. 
        """
        stop_app(stop_app_argparser().parse_args(self.__prog_args))


    def flask_init(self):
        """
        Initialize a dockerized flask application. This app will utilize meinheld, gunicorn, Flask, and profpy. 
        Included in this app directory structure:
            - all docker componenets
            - an app directory with main.py (the controller), templates/, and static/ (which contains js/, css/, and images/)
            - a dba directory with initial setup tools for the database schema
            - a SAMPLE.env file and a .env file with an empty db_password variable
            - .gitignore
            - README.md
            - requirements.txt
            - a base Rowan-styled template system
                - the layout includes bootstrap4, datatables, and select2
        """
        parser = flask_init_argparser()
        if self.__prog_args:
            flask_init(parser.parse_args(self.__prog_args))
        else:
            flask_init(parser.parse_args(flask_init_prompt()))


def main():
    """
    CLI driver
    """
    Cli()
    