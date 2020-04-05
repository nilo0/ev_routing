from setuptools import setup
from distutils.command.build_py import build_py as _build_py
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='ev_routing',
    version='0.0',
    description='Electrical Vehicles (EVs) Routing',
    long_description=read('README.md'),
    url='http://github.com/nilo0/ev_routing',
    keywords='Electrical Vehicles, EV, Routing',
    author='Niloofar Rahmati',
    author_email='nilo0far@zedat.fu-berlin.de',
    license='GPLv3',
    packages=['ev_routing'],
    install_requires=[
        'overpy',
        'plotly',
        'requests',
        'numpy',
        'scipy',
        'pytest',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    zip_safe=False
)
