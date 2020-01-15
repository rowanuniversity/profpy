"""
stop-app command line tool
"""
import subprocess
import pathlib
import argparse
import os


def str_to_pathlib(in_str):
    """
    Handle the str to pathlib.Path casting
    """
    if isinstance(in_str, pathlib.Path):
        return in_str
    else:
        try:
            return pathlib.Path(in_str)
        except:
            raise IOError("Invalid path specified.")


def stop_app(in_args):
    """
    Driver
    """
    os.chdir(str(in_args.app_path))
    subprocess.call(["docker-compose", "down"])


def stop_app_argparser():
    """
    Return the argparser for this tool
    """
    parser = argparse.ArgumentParser(
        description="Stop a dockerized web application that you set up via one of profpy's init tools."
    )
    parser.add_argument("-ap", "--app-path", type=str_to_pathlib, default=pathlib.Path("."), help="Optional path to the app (\".\").")
    return parser
