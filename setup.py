from setuptools import setup

version = "0.1.1"

long_description = """\
Tinman is an take what you need package designed to speed development of
Tornado applications.  It includes an application wrapper and a toolbox of
decorators and utilities.
"""
setup(name='tinman',
      version=version,
      description="Tornado application wrapper and toolbox for \
Tornado development",
      long_description=long_description,
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
      packages=['tinman'],
      requires=['ipaddr', 'pyyaml'],
      entry_points=dict(console_scripts=['tinman=tinman:main']),
      zip_safe=True)
