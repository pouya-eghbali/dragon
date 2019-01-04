# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='dragon-player',
    version="0.6",
    packages=find_packages(),
    include_package_data=False,
    install_requires=["asciimatics", "python_vlc", "beautifulsoup4", "requests", "youtube_dl"],
    entry_points = {
        'console_scripts': ['dragon=dragon_player.cli:main'],
    },
    long_description=long_description,
    long_description_content_type='text/markdown',
    description="The CLI YouTube Player",
    author='Pouya Eghbali',
    author_email='pouya.eghbali@yandex.ch',
    url='https://github.com/pouya-eghbali/dragon',
)
