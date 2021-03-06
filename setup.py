from setuptools import setup, find_packages


def get_requirements():
    with open('requirements.txt') as f:
        return f.read().split()

setup(
    name='tethys',
    version='1.2.0',
    description='Spatial and Temporal Downscaling of Global Water Demands',
    url='https://github.com/JGCRI/tethys',
    packages=find_packages(),
    license='BSD 2-Clause',
    author='Xinya Li; Chris R. Vernon',
    author_email='xinya.li@pnnl.gov;chris.vernon@pnnl.gov',
    install_requires=get_requirements(),
    dependency_links=['git+https://github.com/JGCRI/gcam_reader@master#egg=gcam_reader-0.5.0'],
    include_package_data=True
)
