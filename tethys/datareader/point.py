"""
Helper functions for converting point data to raster
"""

import numpy as np
import pandas as pd
import pyproj


def from_cerf(cerf_df, resolution, years):
    df = cerf_df[['ycoord', 'xcoord', 'tech_name', 'generation_mwh_per_year', 'sited_year', 'retirement_year']]
    transformer = pyproj.Transformer.from_crs('ESRI:102003', 'EPSG:4326', always_xy=True)
    _ = transformer.transform(df['xcoord'], df['ycoord'], inplace=True)
    df = df.rename(columns=dict(xcoord='lon', ycoord='lat', generation_mwh_per_year='value', tech_name='sector'))

    df = pd.concat([df[(df['sited_year'] <= i) & (i < df['retirement_year'])].assign(year=i) for i in years])
    df = df.drop(columns=['sited_year', 'retirement_year'])

    return df_to_raster(df, resolution)


def df_to_raster(df, resolution):
    """

    :param df: pandas dataframe with columns 'sector', 'year', 'lat', 'lon', and 'value'
    :param resolution: target output resolution in degrees
    :return: xarray dataarray with dimensions 'sector', 'year', 'lat', and 'lon'
    """
    df['lat'] = cut_helper(df['lat'], resolution=resolution, n=180)
    df['lon'] = cut_helper(df['lon'], resolution=resolution, n=360)

    da = df.groupby(['sector', 'year', 'lat', 'lon'])['value'].sum().to_xarray()
    da = da.reindex(lat=np.linspace(90 - resolution / 2, -90 + resolution / 2, round(180 / resolution)),
                    lon=np.linspace(-180 + resolution / 2, 180 - resolution / 2, round(360 / resolution)))

    return da


def cut_helper(series, resolution, n):
    """

    :param series: series of latitudes and longitudes
    :param resolution: width of resulting bins in degrees
    :param n: 180 for latitude, 360 for longitude
    :return: series of points rounded to nearest bin
    """

    # compute some values for later
    m = n // 2  # outer edge of last bin
    c = m - (resolution / 2)  # center of last bin
    nbins = round(n / resolution)

    bins = np.linspace(-m, m, nbins + 1)  # bin edges
    labels = np.linspace(-c, c, nbins)  # bin centers

    return pd.cut(series, bins, labels=labels).astype(float)
