import os
from setuptools import setup

with open("../README.md", "r") as fh:
    long_description = fh.read()

setupDirectory = os.path.dirname(os.path.realpath(__file__))

setup(
    name="hypergol",
    version="0.0.3",
    author="Laszlo Sragner",
    author_email="hypergol.developer@gmail.com",
    description="An opinionated multithreaded Data Science framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hypergol/hypergol",
    packages=['hypergol', 'hypergol.cli'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['fire', 'Jinja2', 'GitPython'],
    include_package_data=True
)
