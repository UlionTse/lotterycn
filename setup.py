# coding=utf-8
# author=UlionTse

import re
import pathlib
from setuptools import setup, find_packages


NAME = "lotterycn"
PACKAGE = "lotterycn"

AUTHOR = "UlionTse"
AUTHOR_EMAIL = "shinalone@outlook.com"
HOMEPAGE_URL = "https://github.com/uliontse/lotterycn"
DESCRIPTION = "LotteryCN is a library which aims to bring enjoyable analysis of lottery in Python"
LONG_DESCRIPTION = pathlib.Path('README.md').read_text(encoding='utf-8')
VERSION = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', pathlib.Path('lotterycn/__init__.py').read_text(), re.M).group(1)


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    package_dir={"lotterycn": "lotterycn"},
    url=HOMEPAGE_URL,
    project_urls={
        'Source': 'https://github.com/UlionTse/lotterycn',
        'Changelog': 'https://github.com/UlionTse/lotterycn/blob/master/change_log.txt',
        'Documentation': 'https://github.com/UlionTse/lotterycn/blob/master/README.md',
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords=['lottery'],
    install_requires=[
        'tqdm>=4.64.1',
        'numpy>=1.21.6',
        'pandas>=1.4.0',
        'requests>=2.28.1',
    ],
    python_requires='>=3.6',
    extras_require={'pypi': ['build>=0.8.0', 'twine>=4.0.1']},
    zip_safe=False,
)
