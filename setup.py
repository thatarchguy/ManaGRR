from setuptools import setup

setup(
    name='grrmanager',
    version='0.0.0a',
    long_description=__doc__,
    packages=['app'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask>=0.10.0'
    ],
    test_suite='tests'
)
