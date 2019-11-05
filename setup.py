from setuptools import setup

def readme ():
    try:
        with open('README.rst') as f:
            return f.read()
    except IOError:
        return ''

data_files = ['cravat_multiuser.css', 'cravat_multiuser.js', 'login.html']

setup(
    name='open-cravat-multiuser',
    version='1.6.0',
    description='OpenCRAVAT Multiuser Addon',
    long_description=readme(),
    author='Rick Kim, Kyle Moad, Mike Ryan, and Rachel Karchin',
    author_email='rkim@insilico.us.com',
    url='http://www.opencravat.org',
    license='',
    package_data={
        'cravat_multiuser': data_files,
    },
    install_requires=['aiohttp_session', 'cryptography', 'open-cravat>=1.6.0'],
    packages=['cravat_multiuser'],
    python_requires='>=3.6',
)
