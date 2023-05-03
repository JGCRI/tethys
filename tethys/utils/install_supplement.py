import os
import zipfile
import requests
from importlib.resources import files
from importlib.metadata import version
from io import BytesIO as BytesIO

default_example_dir = os.path.join(str(files('tethys')), 'example')


class InstallSupplement:
    """Download and unpack example data supplement from Zenodo that matches the current installed
    Tethys distribution.
    :param example_data_directory:              Full path to the directory you wish to install
                                                the Tethys example data to.  Must be write-enabled
                                                for the user.
    """

    # URL for DOI minted example data hosted on Zenodo
    DATA_VERSION_URLS = {
        '2.0.0': 'https://zenodo.org/record/7569652/files/example.zip?download=1'
    }

    def __init__(self, example_data_directory):

        # full path to the Tethys root directory where the example dir will be stored
        self.example_data_directory = example_data_directory

    def fetch_zenodo(self):
        """Download and unpack the Zenodo example data supplement for the
        current Tethys distribution."""

        # get the current version of tethys that is installed
        current_version = version('tethys')

        try:
            data_link = InstallSupplement.DATA_VERSION_URLS[current_version]

        except KeyError:
            msg = "Link to data missing for current version:  {}.  Please contact admin."
            raise(msg.format(current_version))

        # retrieve content from URL
        print(f"Downloading example data for Tethys version {current_version}. This might take a few minutes.")
        r = requests.get(data_link)

        with zipfile.ZipFile(BytesIO(r.content)) as zipped:

            # extract each file in the zipped dir to the project
            for f in zipped.namelist():
                print("Unzipped: {}".format(os.path.join(self.example_data_directory, f)))
                zipped.extract(f, self.example_data_directory)


def get_example_data(example_data_directory=None):
    """Download and unpack example data supplement from Zenodo that matches the current installed
    Tethys distribution.

    :param example_data_directory:              Full path to the directory you wish to install
                                                the Tethys example data to.  Must be write-enabled
                                                for the user.

    :type example_data_directory:               str

    """

    if example_data_directory is None:
        example_data_directory = default_example_dir  # tethys package directory

    zen = InstallSupplement(example_data_directory)

    zen.fetch_zenodo()
