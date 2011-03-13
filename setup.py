from setuptools import setup

version = "0.1.0"

long_description = """\
tinman is a set of decorators and utilities to add value to and speed
development of Tornado applications.
"""
setup(name='tinman',
      version=version,
      description="Decorator and utility suite for Tornado",
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
      zip_safe=True)
