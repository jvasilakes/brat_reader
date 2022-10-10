import pathlib
from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(name="pybrat",
      version="0.1.0",
      description="A tool for working with brat annotations in Python.",
      long_description=long_description,
      packages=find_packages())
