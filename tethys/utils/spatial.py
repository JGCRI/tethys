from typing import Union
from pathlib import Path

import hvplot.xarray
import pandas as pd
import rioxarray as rio
import xarray as xr

import tethys
from tethys.utils.region_to_id_mapping import name_to_id_mapping


class InputViewer:
    """View input projection tabular data allocated spatially.

    This class is responsible for visualizing the spatial allocation of
    tabular data related to input projections within a given sector and year.
    """
    def __init__(
        self,
        result_object: tethys.model.Tethys,
        sector: str,
        year: int,
        mapping_dict: Union[dict, None] = None,
        regions_raster_file: Union[str, None] = None
    ):
        """Initialize the InputViewer with the given parameters.

        :param result_object: A Tethys model object containing the result data.
        :type result_object: tethys.model.Tethys
        :param sector: The sector for which the input data is being visualized.
        :type sector: str
        :param year: The year for which the input data is being visualized.
        :type year: int
        :param mapping_dict: Optional; A dictionary mapping region names to IDs. If None, an attempt will be made to auto-detect the mapping.
        :type mapping_dict: dict, optional
        :param regions_raster_file: Optional; The file path to the raster file representing region boundaries. If None, an attempt will be made to auto-detect the file.
        :type regions_raster_file: str, optional
        """
        self.result = result_object
        self.inputs = self.validate_inputs()
        self.sector = sector
        self.year = year
        self.mapping_dict = mapping_dict
        self.regions_raster_file = regions_raster_file
        self.regions_data_array = None
        self.grid = self.generate_grid()

    def validate_inputs(self):
        """Ensure inputs data frame is in the correct format."""
        input_columns = self.result.inputs.columns
        assert "region" in input_columns, "Missing required field in inputs:  'region'"
        assert "sector" in input_columns, "Missing required field in inputs:  'sector'"
        assert "year" in input_columns, "Missing required field in inputs:  'year'"

        return self.result.inputs

    def select_mapping_dict(self):
        """Select the appropriate mapping dictionary to map regions to their ids."""
        # auto-select if mapping is none
        region_names = sorted(self.inputs["region"].unique())

        if region_names == sorted(name_to_id_mapping["region_mapping"].keys()):
            self.mapping_dict = name_to_id_mapping["region_mapping"]
            self.regions_raster_file = Path(self.result.root) / "data/maps/regions.tif"

        elif region_names == sorted(name_to_id_mapping["basin_mapping"].keys()):
            self.mapping_dict = name_to_id_mapping["basin_mapping"]
            self.regions_raster_file = Path(self.result.root) / "data/maps/regionbasins.tif"

        else:
            msg = "Region name to id mapping cannot be auto-detected." + \
            "Please provide a mapping dictionary to `mapping_dict` and the source region raster file to `regions_raster_file`."
            raise KeyError(msg)

    def generate_grid(self):
        """Generate a modified data array that has mapped grid ids to their values."""
        df = self.inputs.loc[
            (self.inputs["sector"] == self.sector) & 
            (self.inputs["year"] == self.year)
        ].copy()
        
        # add in id 
        if self.mapping_dict is None:
            self.select_mapping_dict()
        df["region_id"] = df["region"].map(self.mapping_dict)
        
        # generate mapping from region_id to value
        value_mapping = df.set_index("region_id")["value"].to_dict()

        # read in raster to data array
        self.regions_data_array = rio.open_rasterio(self.regions_raster_file)

        # map to grid
        mapping = self.regions_data_array.to_series().map(value_mapping).to_xarray()
        return xr.DataArray(
            mapping, 
            coords=self.regions_data_array.coords, 
            dims=self.regions_data_array.dims, 
            name="inputs"
        )

    def plot(
        self, 
        width: int = 1000, 
        height: int = 600, 
        cnorm: Union[str, None] = None,
        cmap: str = "viridis_r"
    ):
        """Generate an interactive plot.

        :param width: Width of the plot in pixels, defaults to 1000.
        :type width: int, optional
        :param height: Height of the plot in pixels, defaults to 600.
        :type height: int, optional
        :param cnorm: Normalization for the colormap, can be a string or None, defaults to None.
        :type cnorm: Union[str, None], optional
        :param cmap: Colormap to use for the plot, defaults to "viridis_r".
        :type cmap: str, optional
        :return: An interactive plot object.
        :rtype: hvPlot
        """
        return self.grid.sel(band=1).hvplot(
            cnorm=cnorm,
            cmap=cmap,
            x="x",
            y="y",
            width=width,
            height=height,
            title=f"Sector: {self.sector}, Year: {self.year}"
        )

    def to_raster(
        self,
        output_raster_path: str
    ):
        """Write the raster data to a file.

        :param output_raster_path: The file path where the raster will be saved.
        :type output_raster_path: str
        """
        self.grid.sel(band=1).rio.to_raster(output_raster_path)
