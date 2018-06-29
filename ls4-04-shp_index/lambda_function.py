# --------------- IMPORTS ---------------
import os
import boto3
import geopandas as gpd
import rasterio
from shapely.geometry import box
from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import create_engine

# Database Connection Info
driver = os.environ.get('DB_DRIVER')
database = os.environ.get('DB_NAME')
username = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
host = os.environ.get('DB_HOST')
port = os.environ.get('DB_PORT')

engine_string = '%s://%s:%s@%s:%s/%s' % (driver, username, password,
                                         host, port, database)
engine = create_engine(engine_string)

# --------------- Main handler ------------------

def lambda_handler(event, context):
    print(event)
    print(context)
    # establish some variables
    source_bucket = event['sourceBucket']
    source_key = event['sourceKey']

    # verify input is a cog
    if 'cog/' not in source_key:
        print("source key is not cog! exiting...")
        print(source_key)
        return

    filename = source_key.split("/")[-1]
    key_path = source_key.replace(filename, '')
    print(key_path)
    # connect to s3
    client = boto3.client('s3')
    # gather a list of keys in the COG sub directory for the collection
    cog_keys = []
    def get_keys(token=''):
        if token == '':
            response = client.list_objects_v2(Bucket=source_bucket,
                                              Prefix=key_path)
        else:
            response = client.list_objects_v2(Bucket=source_bucket,
                                              Prefix=key_path,
                                              ContinuationToken=token)
        print(response)
        for cog in response['Contents']:
            prefix = 's3://' + source_bucket + '/'
            s3_path = prefix + cog['Key']
            if 'tile_index' not in s3_path:
                cog_keys.append(s3_path)
        if 'NextContinuationToken' in response.keys():
            get_keys(response['NextContinuationToken'])
    get_keys()
    print(str(len(cog_keys)) + " COG keys found.")

    # setup upload keys
    band = source_key.split("/")[0]
    band_pre = band + "/"
    index_name = key_path.replace(band_pre, '').replace('/cog/', '').replace('/', '_')
    print(index_name)
    shp_key = key_path + "tile_index/" + index_name
    print(shp_key)

    # setup container for shapefile data
    df = gpd.GeoDataFrame(columns=['location','src_srs','dl_orig','dl_georef','geometry'])
    src_srs = "EPSG:3857"
    # file shapefile data container
    for key in cog_keys:
        with rasterio.open(key) as dataset:
            location = key.replace('s3://', '/vsis3/')
            dl_orig = key.replace('s3://', 'https://s3.amazonaws.com/').replace('cog/', 'scanned/')
            dl_georef = key.replace('s3://', 'https://s3.amazonaws.com/')
            bounds = dataset.bounds
            df = df.append({'location':location, 'src_srs': src_srs, 'dl_orig': dl_orig, 'dl_georef': dl_georef, 'geometry': box(bounds[0], bounds[1], bounds[2], bounds[3])},ignore_index=True)

    # create shapefile for s3
    df.to_file("/tmp/tile_index.shp")

    # upload shapefile to s3
    shp_suffixes = ['.cpg', '.dbf', '.shp', '.shx']
    for sfx in shp_suffixes:
        filename = '/tmp/tile_index' + sfx
        keyname = shp_key + sfx
        print('uploading: ' + keyname)
        client.upload_file(filename, source_bucket, keyname, ExtraArgs={'ACL':'public-read'})
    print("upload success!")

    # upload geodataframe to postgis
    df['geom'] = df['geometry'].apply(lambda x: WKTElement(x.wkt, srid=3857))
    df.drop('geometry', 1, inplace=True)
    print('geom reformatted')
    df.to_sql(table_name, engine, if_exists='replace', index=True, index_label='oid', dtype={'geom': Geometry('POLYGON', srid=3857)})
    print('tile index added to postgis!')

if __name__ == '__main__':
    lambda_handler(event='event', context='context')
