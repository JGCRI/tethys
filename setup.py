from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


def get_requirements():
    with open('requirements.txt') as f:
        return f.read().split()


setup(
    name='demeterw',
    version='1.0.0',
    packages=find_packages(),
    url='',
    license='BSD 2-Clause',
    author='Xinya Li; Chris R. Vernon',
    author_email='xinya.li@pnnl.gov;chris.vernon@pnnl.gov',
    description='Spatial and Temporal Downscaling of Global Water Demands',
    long_description=readme(),
    install_requires=get_requirements()
)