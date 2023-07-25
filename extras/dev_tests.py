# Alt + Shift + E to run each line
# Version 2.0 Getting STarted DOcs tests
import tethys
import os

# Example test Power plant downscaling
import pandas as pd
from tethys.datareader.point import df_to_raster
import xarray as xr
global_power_plant_database = "C:/Z/models/tethysExampleFolders/global_power_plant_database.csv"
df = pd.read_csv(global_power_plant_database)
df = df.rename(columns=dict(longitude='lon', latitude='lat', capacity_mw='value', primary_fuel='sector'))
df["year"] = 2015
output = df_to_raster(df, 0.5)
output = output.to_dataset("sector")
output.to_netcdf("C:/Z/models/tethysExampleFolders/global_power_plant_database.nc4", encoding={variable: {'zlib': True, 'complevel': 5} for variable in output})
list(output.keys())
config_file = 'C:/Z/models/tethysExampleFolders/example/config_wri_power.yml'
result = tethys.run_model(config_file)

# View Outputs in Console
result.outputs # xarray file with all outputs
list(result.outputs.keys()) # Get list of variables
result.outputs.electricity_solar # View Municipal xarray
result.outputs.electricity_solar.sel(year=2030) # Check one year
# Plot Outputs
from matplotlib import colors, pyplot as plt
plt.figure(figsize=(10, 6), dpi=300) # higher dpi in order to see resolution
# # powernorm the color palette in order to see more detail at the low end
# result.outputs.Municipal.sel(year=2010).plot(norm=colors.PowerNorm(0.25), cmap='viridis_r')
mask = result.region_masks.any(dim='region').compute()
result.outputs.electricity_solar.sel(year=2030).where(mask).plot(norm=colors.PowerNorm(0.25), cmap='viridis_r')
# plt.show() # To show in pycharm
plt.savefig(fname="plot.png") # To plot result
plt.show()

# Example for CERF data
import pandas as pd
from tethys.datareader.point import from_cerf
cerf_data = "cerf_file.csv" # Could be csv or python pandas dataframe
output = from_cerf(cerf_data, 0.5, [2030,2035])
output.to_netcdf("C:/Z/models/tethysExampleFolders/cerf.nc4", encoding={variable: {'zlib': True, 'complevel': 5} for variable in output})
list(output.keys())
config_file = 'C:/Z/models/tethysExampleFolders/example/config_cerf.yml' # Need to build this and replace with relevant cerf.ncdf
result = tethys.run_model(config_file)
