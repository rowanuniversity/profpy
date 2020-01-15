"""
run-app command line tool
"""
import subprocess
import pathlib
import argparse
import os

def validate_instance(in_instance):
    """
    Check that the user provided a valid instance
    """
    if not in_instance:
        return "dev"
    else:
        i = in_instance.lower()
        if i in ["prod", "test", "dev"]:
            return i
        else:
            raise IOError("Invalid instance. Must be dev, test, or prod.")


def str_to_pathlib(in_str):
    """
    Handle the string to pathlib.Path casting
    """
    if isinstance(in_str, pathlib.Path):
        return in_str
    else:
        try:
            return pathlib.Path(in_str)
        except:
            raise IOError("Invalid path specified.")


def run_app(in_args):
    """
    Driver
    """
    path = in_args.app_path
    os.chdir(str(path))

    env = in_args.instance
    override = str(pathlib.Path(".", "docker-overrides", f"{env}.docker-compose.override.yml"))
    cmd = [
        "docker-compose", "-f", "docker-compose.yml", "-f", override, "up", "--build"
    ]
    if in_args.detach or in_args.instance in ["prod", "test"]:
        cmd.append("-d")
    if in_args.force_recreate:
        cmd.append("--force-recreate")
    subprocess.call(cmd)


def run_app_argparser():
    """
    Return the argparser for this tool
    """
    parser = argparse.ArgumentParser(
        description="Run a dockerized web application that you set up via one of profpy's init tools."
    )
    parser.add_argument("instance", type=validate_instance, help="The instance to run this on.", nargs="?", default="dev")
    parser.add_argument("-ap", "--app-path", type=str_to_pathlib, default=pathlib.Path("."), help="Optional path to the app (\".\").")
    parser.add_argument("--force-recreate", action="store_true", required=False, help="Force a full recreate via docker-compose.")
    parser.add_argument("-d", "--detach", action="store_true", required=False, help="Run the container in detached mode.")
    return parser
