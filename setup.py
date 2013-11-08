import os
from platform import python_version_tuple
from setuptools import setup
import sys

requirements = ['helper', 'pyyaml', 'tornado>=3.1']
test_requirements = ['mock', 'nose']
(major, minor, rev) = python_version_tuple()
if float('%s.%s' % (major, minor)) < 2.7:
    requirements.append('importlib')
    test_requirements.append('unittest2')

# Build the path to install the templates, example config and static files
if hasattr(sys, 'real_prefix'):
    base_path = 'share/tinman'
else:
    base_path = '/usr/share/tinman'

data_files = {'%s/' % base_path: ['README.md', 'LICENSE', 'etc/example.yaml'],
              '%s/init.d/' % base_path: ['etc/init.d/tinman'],
              '%s/sysconfig/' % base_path: ['etc/sysconfig/tinman']}

with open('MANIFEST.in', 'w') as handle:
    for path in data_files:
        for filename in data_files[path]:
            handle.write('include %s\n' % filename)

setup(name='tinman',
      version='0.10.0p3',
      description=("Tornado application wrapper and toolset for Tornado "
                   "development"),
      long_description=('Tinman is a take what you need package designed to '
                        'speed development of Tornado applications. It '
                        'includes an application wrapper and a toolbox of '
                        'decorators and utilities.'),
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
      ],
      keywords='tornado',
      author='Gavin M. Roy',
      author_email='gavinmroy@gmail.com',
      url='http://github.com/gmr/tinman',
      license=open('LICENSE').read(),
      packages=['tinman',
                'tinman.auth',
                'tinman.decorators',
                'tinman.handlers',
                'tinman.loaders',
                'tinman.utilities'],
      install_requires=requirements,
      extras_require={'Heapy': 'guppy',
                      'LDAP': 'python-ldap',
                      'MsgPack': 'msgpack',
                      'NewRelic': 'newrelic',
                      'PostgreSQL': 'psycopg2',
                      'RabbitMQ': 'pika',
                      'Redis': 'tornado-redis',
                      'Redis Sessions': 'tornado-redis',
                      'Whitelist': 'ipaddr'},
      test_suite='nose.collector',
      tests_require=test_requirements,
      data_files=[(key, data_files[key]) for key in data_files.keys()],
      entry_points=dict(console_scripts=['tinman=tinman.controller:main',
                                         'tinman-init=tinman.utilities.'
                                         'initialize:main',
                                         'tinman-heap-report=tinman.utilities.'
                                         'heapy_report:main']),
      zip_safe=True)
