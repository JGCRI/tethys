from setuptools import setup, find_packages

def get_requirements():
    with open('requirements.txt') as f:
        return f.read().split()

setup(
    name='demeter-w',
    version='1.0.0',
	description='Spatial and Temporal Downscaling of Global Water Demands',
	url='https://github.com/JGCRI/demeter-w',
    packages=find_packages(),
    license='BSD 2-Clause',
    author='Xinya Li; Chris R. Vernon',
    author_email='xinya.li@pnnl.gov;chris.vernon@pnnl.gov',
    install_requires=get_requirements(),
	include_package_data=True
)