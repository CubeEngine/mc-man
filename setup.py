""" Setup file for PlugMan """
from distutils.core import setup
import mcman

setup(
    name='mcman',
    version=mcman.__version__,
    author=mcman.__author__,
    author_email='mail@totokaka.io',
    description='A Minecraft server jar and plugins manager',
    url='https://github.com/CubeEngineDev/mcman',
    packages=['mcman'],
    scripts=["bin/mcman"],
    install_requires=[
        'pyyaml',
        'pybukget',
        'pyspacegdn'
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],
)
