from setuptools import setup
import os

def readme ():
    try:
        with open('README.rst') as f:
            return f.read()
    except IOError:
        return ''

data_files = ['favicon.ico', 'favicon.png', 'logout.png', 'pwchng.png']
for root, dirs, files in os.walk(os.path.join('cravat_multiuser', 'nocache')):
    root_files = [os.path.join('..', root, f) for f in files]
    data_files.extend(root_files)

setup(
    name='open-cravat-multiuser',
    version='2.2.9',
    description='OpenCRAVAT Multiuser Addon',
    long_description=readme(),
    author='Rick Kim, Kyle Moad, Mike Ryan, and Rachel Karchin',
    author_email='rkim@insilico.us.com',
    url='http://www.opencravat.org',
    license='',
    package_data={
        'cravat_multiuser': data_files,
    },
    install_requires=[
        'aiohttp_session', 
        'cryptography', 
        'open-cravat>=2.2.2'
    ],
    packages=['cravat_multiuser'],
    python_requires='>=3.6',
)
