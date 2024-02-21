import importlib.resources
import importlib.metadata
from pathlib import Path
import requests
from typing import Union
import zipfile
import os
from io import BytesIO

from tqdm import tqdm


default_download_dir = str(importlib.resources.files('tethys'))

# URL for DOI minted example data hosted on Zenodo
DATA_VERSION_URLS = {
    '2.0.0': 'https://zenodo.org/record/7569652/files/example.zip?download=1',
    '2.0.1': 'https://zenodo.org/record/7569652/files/example.zip?download=1',
    '2.0.2': 'https://zenodo.org/record/7569652/files/example.zip?download=1',
}


def get_example_data(
    download_first: bool = False, 
    example_data_directory: Union[None, str] = None
):
    """
    Download and unpack example data supplement from a specified URL.

    This function downloads a data supplement from Zenodo that matches the current installed Tethys 
    distribution and optionally extracts it to a specified directory.

    :param url:                         The URL from which to download the example data.
    :type url:                          str
    
    :param download_first:              A flag indicating whether to extract the downloaded data only or download it first. 
                                        If True, the zipped directory will be downloaded first and then extracted.
                                        Defaults to False.
    :type extract:                      bool

    :param example_data_directory:      The full path to the directory where the example data should be 
                                        installed. If None, the default Tethys directory is used. 
                                        The directory must be write-enabled for the user.
    :type example_data_directory:       Union[None, str], optional
    """
    if example_data_directory is None:
        example_data_directory = default_download_dir

    # get the current version of tethys that is installed
    current_version = importlib.metadata.version('tethys')

    try:
        url = DATA_VERSION_URLS[current_version]

    except KeyError:
        msg = "Link to data missing for current version:  {}.  Please contact admin."
        raise(msg.format(current_version))

    print(f"Downloading example data for Tethys version {current_version}.")

    if download_first:

        local_filename = Path(example_data_directory) / url.split('/')[-1].split('?')[0]
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size_in_bytes = int(r.headers.get('content-length', 0))
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    progress_bar.update(len(chunk))
                    f.write(chunk)
            progress_bar.close()

        print(f"Downloaded {local_filename}")

        # Extract the file to the example_data_directory and delete the zipped file after extracting
        with zipfile.ZipFile(local_filename, 'r') as zip_ref:
            zip_ref.extractall(example_data_directory)

        # delete zipped file after extraction
        local_filename.unlink()

        print(f"Extracted {local_filename} to {example_data_directory} and deleted the zipped file")

    else:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

        with BytesIO() as file_stream:
            for data in response.iter_content(chunk_size=1024):
                progress_bar.update(len(data))
                file_stream.write(data)
            progress_bar.close()
            file_stream.seek(0)  # Seek to the beginning of the file
            with zipfile.ZipFile(file_stream) as z:
                z.extractall(path=example_data_directory)

        print(f"Extracted contents to {example_data_directory}")
