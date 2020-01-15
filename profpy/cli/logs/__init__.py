"""
logs command line tool
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


def logs(in_args):
    """
    Driver
    """
    os.chdir(str(in_args.app_path))
    cmd = ["docker-compose", "logs"]
    for flag in ["no_color", "follow", "timestamps"]:
        if getattr(in_args, flag):
            cmd.append(f"--{flag.replace('_', '-')}")
    if in_args.tail:
        cmd.append(f"--tail={in_args.tail}")
    subprocess.call(cmd)


def validate_tail(in_tail):
    """
    Validate the --tail input
    """
    if isinstance(in_tail, int):
        return in_tail
    else:
        if in_tail == "all":
            return in_tail
        else:
            try:
                out_tail = int(in_tail)
                if out_tail > 0:
                    return out_tail
                else:
                    raise IOError("Invalid tail specified. Must be a positive integer or \"all\"")
            except ValueError:
                raise IOError("Invalid tail specified. Must be a positive integer or \"all\"")

def logs_argparser():
    """
    Return the argparser for this tool
    """
    parser = argparse.ArgumentParser(
        description="Get the logs for an app you created with a profpy init tool."
    )
    parser.add_argument("-f", "--follow", action="store_true", required=False, help="Follow log output")
    parser.add_argument("-t", "--timestamps", action="store_true", required=False, help="Show timestamps")
    parser.add_argument("--tail", default="all", type=validate_tail, help="Number of lines to show from the end of the logs")
    parser.add_argument("--no-color", action="store_true", required=False, help="Produce monochrome output")
    parser.add_argument("-ap", "--app-path", type=str_to_pathlib, default=pathlib.Path("."), help="Optional path to the app (\".\").")
    return parser
