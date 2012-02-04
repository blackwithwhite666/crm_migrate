#!/usr/bin/env python

import sys

from setuptools import setup, find_packages


long_description = open('README').read()

setup(
    name='crm_migrate',
    version='0.1',
    description='crm_migrate is a simple tool for virtual machine configuration with pacemaker, libvirt and DRBD.',
    long_description=long_description,
    author='Lipin Dmitriy',
    author_email='blackwithwhite666@gmail.com',
    url='https://github.com/blackwithwhite666/crm_migrate',
    packages=find_packages(),
    install_requires=['paramiko'],
    entry_points={
        'console_scripts': [
            'migrate-vm = crm_migrate.cli:main',
        ]
    },
    classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: Linux',
          'Programming Language :: Python',
          'Topic :: System :: Clustering',
          'Topic :: System :: Systems Administration',
    ],
)