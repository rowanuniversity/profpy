import os
from setuptools import setup


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name='profpy',
    version='0.2.0',
    packages=['profpy', 'profpy.db', 'profpy.db.fauxrm', 'profpy.db.fauxrm.queries', 'profpy.db.fauxrm.handlers', 'profpy.db.general', 'profpy.apis', 'profpy.apis.utils'],
    url='',
    license='',
    author='Connor Hornibrook',
    author_email='hornibrookc@rowan.edu',
    description='',
    long_description=read("README.md")
)
