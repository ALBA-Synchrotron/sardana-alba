import sys
from setuptools import setup, find_packages


setup(
    name="sardana-alba",
    version="0.9.0",
    description="ALBA specific sardana tools (controllers, macros, tools)",
    author="ALBA controls team",
    author_email="controls@cells.es",
    license="GPLv3",
    url="http://github.com/ALBA-Synchrotron/sardana-alba",
    packages=find_packages(),
    install_requires=["sardana"],
    extras_require=["tangoctl>=0.6"],
    python_requires=">=3.5",
)
