""" Setup file for PlugMan """
from distutils.core import setup
import mcman

setup(
    name='mcman',
    version=mcman.__version__,
    author=mcman.__author__,
    author_email='mail@totokaka.io',
    description='A Minecraft server jar and plugins manager',
    # TODO - url='-',
    packages=['mcman'],
    scripts=["bin/mcman"],
    requires=[
        'pyyaml',
        'pybukget',
        'pyspacegdn'
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],
)
