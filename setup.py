# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from iparrot import __name__, __version__, __author__

with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name=__name__,
    version=__version__,
    author=__author__,
    author_email="i@idleman.club",
    description="Automated test solution for http requests based on recording and playback",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    keywords="record replay playback parrot automation http",

    url="https://github.com/idle-man/iParrot",
    project_urls={
        "Bug Tracker": "https://github.com/idle-man/iParrot/issues",
        "Documentation": "https://github.com/idle-man/iParrot/blob/master/README.md",
        "Source Code": "https://github.com/idle-man/iParrot",
    },
    license="MIT",

    packages=find_packages(),
    install_requires=['requests', 'PyYAML'],
    entry_points={
        'console_scripts': [
            'parrot=iparrot.parrot:main',
            'iparrot=iparrot.parrot:main'
        ],
    },
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
        ),
)
