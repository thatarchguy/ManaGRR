from setuptools import setup

setup(
    name='managrr',
    version='1.0.0',
    long_description=__doc__,
    packages=['managrr'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask>=0.10.0'
    ],
    test_suite='tests'
)
