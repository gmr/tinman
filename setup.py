import os
from platform import python_version_tuple
from setuptools import setup

requirements = ['clihelper',
                'ipaddr',
                'python_daemon',
                'pyyaml',
                'tornado']
test_requirements = ['mock', 'nose']
if float('%s.%s' % python_version_tuple()[0:2]) < 2.7:
    requirements.append('argparse')
    test_requirements.append('unittest2')

# Build the path to install the templates, example config and static files
base_path = '/usr/local/share/tinman'

data_files = {'%s/' % base_path: ['README.md', 'etc/example.yaml'],
              '%s/init.d/' % base_path: ['etc/init.d/tinman'],
              '%s/sysconfig/' % base_path: ['etc/sysconfig/tinman']}

with open('MANIFEST.in', 'w') as handle:
    for path in data_files:
        for filename in data_files[path]:
            handle.write('include %s\n' % filename)

setup(name='tinman',
      version='0.9.2',
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
      license='BSD',
      packages=['tinman',
                'tinman.auth',
                'tinman.decorators',
                'tinman.handlers',
                'tinman.loaders',
                'tinman.session',
                'tinman.utilities'],
      install_requires=requirements,
      extras_require={'LDAP': 'python-ldap',
                      'MsgPack Sessions': 'msgpack',
                      'PostgreSQL': 'psycopg2',
                      'RabbitMQ': 'pika',
                      'Redis': 'tornado-redis'},
      test_suite='nose.collector',
      tests_require=test_requirements,
      data_files=[(key, data_files[key]) for key in data_files.keys()],
      entry_points=dict(console_scripts=['tinman=tinman.controller:main',
                                         'tinman-init=tinman.utilities.'
                                         'initialize:main']),
      zip_safe=True)
