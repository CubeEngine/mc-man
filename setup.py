from distutils.core import setup

setup(
    name= 'plugman',
    version= '0.1',
    author= 'totokaka',
    author_email= 'ttotokaka@gmail.com',
    description= 'A bukkit plugin manager written in Python 3',
    url= 'https://github.com/CubeEngineDev/PlugMan',
    packages= ['plugman', 'bukget'],
    scripts=["bin/plugman"],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],
)
