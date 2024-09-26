from setuptools import setup, find_packages
from sammmanager import __version__
import re, os

if __name__ == "__main__":
    setup(
        name='sammmanager',
        version=__version__,
        packages=find_packages(include=['sammmanager', 'sammmanager.*']),
        scripts=[
            'scripts/manager.py'
            ],
        data_files=[],
        install_requires=[ "uwsgi", "urllib3" ]
    )
