import os
from setuptools import setup


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name="profpy",
    version="1.0",
    packages=[
        "profpy",
        "profpy.db",
        "profpy.db.fauxrm",
        "profpy.db.fauxrm.queries",
        "profpy.db.fauxrm.handlers",
        "profpy.db.general",
        "profpy.apis",
        "profpy.apis.utils",
    ],
    url="https://github.com/rowanuniversity/profpy/",
    license="MIT",
    author="Connor Hornibrook",
    author_email="hornibrookc@rowan.edu",
    install_requires=["cx_Oracle", "requests"],
    description="",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
)
