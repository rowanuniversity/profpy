import os
import pathlib
from setuptools import setup


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
    version="2.1.0",
    python_requires=">=3.6.7",
    packages=[
        "profpy",
        "profpy.db",
        "profpy.db.general",
        "profpy.apis",
        "profpy.apis.utils",
        "profpy.web",
        "profpy.web.auth"
    ],
    url="https://github.com/rowanuniversity/profpy/",
    license="MIT",
    author="Connor Hornibrook",
    author_email="hornibrookc@rowan.edu",
    install_requires=requirements(),
    description="",
    long_description=read("pypi.md"),
    long_description_content_type="text/markdown",
)