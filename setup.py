#!/usr/bin/env python
from setuptools import setup, find_packages

libraries = [l.strip() for l in open('requirements.txt').readlines()]

# To set __version__
__version__ = 'unknown'
execfile('padlocker-client/_version.py')

setup(
    name = "padlocker-client",
    version = __version__,
    packages = find_packages(),
    entry_points = {
        "console_scripts": [
            "padlocker-client = padlocker-client.padlocker-client:main",
        ],
    },
    author = "Urban Airship",
    description = "Key Dispersion Service - Client",
    include_package_data = True,
    install_requires = libraries,
    zip_safe = False,
)
