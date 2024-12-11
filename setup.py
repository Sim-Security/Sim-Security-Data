# setup.py
from setuptools import setup, find_packages

setup(
    name="audit_processing",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'gitpython>=3.1.0',
        'pypdf2>=3.0.0',
        'pandas>=1.5.0',
        'numpy>=1.20.0',
        'tqdm>=4.65.0',
    ],
)