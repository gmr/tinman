"""Create a new tinman/tornado project including setting up the setup.py file,
initial directory structure and virtual environment, if desired.

"""
import argparse
import logging
import os
from os import path
import sys


DESCRIPTION = ('A tool to create a new tinman project, including the directory '
               'structure, setup.py file and skeleton configuration')
LOGGER = logging.getLogger(__name__)

from tinman import __version__


class Project(object):

    DEFAULT_MODE = 0755
    DIRECTORIES = ['etc',
                   'source', 'source/less', 'source/js',
                   'static', 'static/css', 'static/img', 'static/js',
                   'templates',
                   'tests']

    def __init__(self):
        self._parser = self._create_argument_parser()

    def _add_base_arguments(self, parser):
        """Add the base arguments to the argument parser.

        :param argparse.ArgumentParser parser: The parser to add arguments to

        """
        parser.add_argument('--version',
                            help='show the version number and exit',
                            action='version',
                            version='%(prog)s ' + __version__)

    def _add_required_arguments(self, parser):
        """Add the required arguments to the argument parser.

        :param argparse.ArgumentParser parser: The parser to add arguments to

        """
        parser.add_argument('project',
                            metavar='PROJECT',
                            help='The project to create')

    def _create_argument_parser(self):
        """Create and return the argument parser with all of the arguments
        and configuration ready to go.

        :rtype: argparse.ArgumentParser

        """
        parser = self._new_argument_parser()
        self._add_base_arguments(parser)
        self._add_required_arguments(parser)
        return parser

    def _create_base_directory(self):
        os.mkdir(self._arguments.project, self.DEFAULT_MODE)

    def _create_directories(self):
        self._create_base_directory()
        self._create_subdirectory(self._arguments.project)
        for directory in self.DIRECTORIES:
            self._create_subdirectory(directory)

    def _create_package_init(self):
        with open('%s/%s/__init__.py' %
                  (self._arguments.project,
                   self._arguments.project), 'w') as init:
            init.write('')

    def _create_package_setup(self):

        template = """from setuptools import setup
import os
from platform import python_version_tuple

requirements = ['tinman']
test_requirements = ['mock', 'nose']
if float('!s.!s' ! python_version_tuple()[0:2]) < 2.7:
    requirements.append('argparse')
    test_requirements.append('unittest2')

# Build the path to install the templates, example config and static files
base_path = '/usr/share/%(project)s'
data_files = dict()
data_paths = ['static', 'templates', 'etc']
for data_path in data_paths:
    for dir_path, dir_names, file_names in os.walk(data_path):
        install_path = '!s/!s' ! (base_path, dir_path)
        if install_path not in data_files:
            data_files[install_path] = list()
        for file_name in file_names:
            data_files[install_path].append('!s/!s' ! (dir_path, file_name))
with open('MANIFEST.in', 'w') as handle:
    for path in data_files:
        for filename in data_files[path]:
            handle.write('include !s\\n' ! filename)


setup(name='%(project)s',
      version='1.0.0',
      packages=['%(project)s'],
      install_requires=requirements,
      test_suite='nose.collector',
      tests_require=test_requirements,
      data_files=[(key, data_files[key]) for key in data_files.keys()],
      zip_safe=True)

"""
        setup_py = template % {'project': self._arguments.project}
        print setup_py
        with open('%s/setup.py' % self._arguments.project, 'w') as init:
            init.write(setup_py.replace('!', '%'))

    def _create_subdirectory(self, subdir):
        os.mkdir('%s/%s' % (self._arguments.project, subdir), self.DEFAULT_MODE)

    def _new_argument_parser(self):
        """Return a new argument parser.

        :rtype: argparse.ArgumentParser

        """
        return argparse.ArgumentParser(prog='tinman-init',
                                       conflict_handler='resolve',
                                       description=DESCRIPTION)


    def run(self):
        self._arguments = self._parser.parse_args()
        self._create_directories()
        self._create_package_init()
        self._create_package_setup()


def initialize_project():
    initializer = Project()
    initializer.run()


if __name__ == '__main__':
    initialize_project()
