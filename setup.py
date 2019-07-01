from setuptools import setup

def readme ():
    try:
        with open('README.rst') as f:
            return f.read()
    except IOError:
        return ''

data_files = ['cravatserver.css', 'cravatserver.js', 'login.html']

setup(
    name='open-cravat-server',
    version='1.6.0',
    description='OpenCRAVAT Server',
    long_description=readme(),
    author='Rick Kim, Kyle Moad, Mike Ryan, and Rachel Karchin',
    author_email='rkim@insilico.us.com',
    url='http://www.opencravat.org',
    license='',
    package_data={
        'cravatserver': data_files,
    },
    #install_requires=['aiohttp_session', 'cryptography', 'open-cravat>=1.6.0'],
    install_requires=['aiohttp_session', 'cryptography',],
    packages=['cravatserver'],
    python_requires='>=3.6',
)
