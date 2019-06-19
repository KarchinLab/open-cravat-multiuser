from setuptools import setup

def readme ():
    try:
        with open('README.rst') as f:
            return f.read()
    except IOError:
        return ''

setup(
    name='open-cravat-server-addon',
    version='1.6.0',
    description='Server Addon for OpenCRAVAT',
    long_description=readme(),
    author='Rick Kim, Kyle Moad, Mike Ryan, and Rachel Karchin',
    author_email='rkim@insilico.us.com',
    url='http://www.opencravat.org',
    license='',
    install_requires=['aiohttp_session', 'cryptography'],
    packages=['cravatserveraddon'],
    python_requires='>=3.6',
)
