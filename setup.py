import os
import pathlib
from setuptools import setup
from profpy import __version__


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


def requirements():
    with open(str(pathlib.PurePath(__file__).parent / "requirements.txt"), "r") as req_file:
        out = []
        for line in req_file.readlines():
            out.append(line.replace("\n", ""))
        return out


setup(
    name="profpy",
    version=__version__,
    python_requires=">=3.6.7",
    packages=[
        "profpy",
        "profpy.db",
        "profpy.db.general",
        "profpy.apis",
        "profpy.apis.utils",
        "profpy.web",
        "profpy.cli", 
        "profpy.cli.flask_init",
        "profpy.cli.run_app",
        "profpy.cli.stop_app",
        "profpy.cli.logs"
    ],
    entry_points={
        "console_scripts": [
            "profpy = profpy.__main__:main"
        ]
    },
    url="https://github.com/rowanuniversity/profpy/",
    license="MIT",
    author="Connor Hornibrook",
    author_email="hornibrookc@rowan.edu",
    install_requires=requirements(),
    description="",
    include_package_data=True,
    long_description=read("pypi.md"),
    long_description_content_type="text/markdown",
)