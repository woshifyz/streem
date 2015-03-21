from setuptools import setup, find_packages

setup(name='streem',
    version='1.0',
    description='Streem Language',
    author='woshifyz',
    author_email='monkey.d.pandora@gmail.com',
    url='https://github.com/woshifyz/streem',
    keywords = "streem language, python awk",
    packages = find_packages('src'),
    package_dir = {'':'src'},
    scripts=['bin/streem'],
    install_requires=[
        'pyparsing'
    ]
)
