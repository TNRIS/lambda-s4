# --------------- IMPORTS ---------------
import os
import boto3
import geopandas as gpd
import rasterio
from shapely.geometry import box

# --------------- Main handler ------------------

def lambda_handler(event='event', context='context'):
    print(event)
    input = 's3://tnris-ls4/bw/countyDelete/agencyDelete_YYYY/frames/cog/02-08-60_6-107.tif'

    df = gpd.GeoDataFrame(columns=['location','src_srs','geometry'])
    src_srs = "EPSG:3857"
    with rasterio.open(input) as dataset:
        print(dataset.profile)
        location = input.replace('s3://', '/vsis3/')
        bounds = dataset.bounds
        df = df.append({'location':location, 'src_srs': src_srs, 'geometry': box(bounds[0], bounds[1], bounds[2], bounds[3])},ignore_index=True)
    df.to_file("test_index.shp")

if __name__ == '__main__':
    lambda_handler()
