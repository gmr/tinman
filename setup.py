from setuptools import setup
from tinman import __version__


setup(name='tinman',
      version=__version__,
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
      author_email='gmr@myyearbook.com',
      url='http://github.com/gmr/tinman',
      license='BSD',
      packages=['tinman', 'tinman.clients'],
      install_requires=['clihelper',
                        'ipaddr',
                        'python_daemon',
                        'pyyaml',
                        'tornado'],
      extras_require={'RabbitMQ': 'pika',
                      'PostgreSQL': 'psycopg2',
                      'LDAP': 'ldap',
                      'Redis': 'brukva'},
      test_suite='nose.collector',
      tests_require=['mock', 'nose', 'coverage', 'unittest2'],
      data_files=[('/usr/local/share/tinamn/init.d',
                   ['etc/init.d/tinman']),
                  ('/usr/local/share/tinamn/',
                   ['etc/example.yaml', 'README.md']),
                  ('/usr/local/share/tinamn/sysconfig',
                   ['etc/sysconfig/tinman'])],
      entry_points=dict(console_scripts=['tinman=tinman.controller:main']),
      zip_safe=True)
