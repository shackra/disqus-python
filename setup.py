#!/usr/bin/env python

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        import sys
        sys.exit(pytest.main(self.test_args))


setup(
    name='shackra-disqus-python',
    version='0.5.0',
    author='shackra',
    author_email='elcorreo@deshackra.com',
    url='https://github.com/shackra/disqus-python',
    description='Disqus API Bindings, updated and compatible with Python 3.x',
    packages=find_packages(),
    zip_safe=False,
    license='Apache License 2.0',
    install_requires=[],
    setup_requires=[],
    tests_require=[
        'pytest',
        'mock',
    ],
    cmdclass={'test': PyTest},
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
)
