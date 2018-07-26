# --------------- IMPORTS ---------------
import os
import zipfile
import boto3
import geopandas as gpd
import gdal
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
        for cog in response['Contents']:
            prefix = '/vsis3/' + source_bucket + '/'
            s3_path = prefix + cog['Key']
            if 'tile_index' not in s3_path and s3_path[-4:] != 'cog/':
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
    df = gpd.GeoDataFrame(columns=['location','src_srs','date','roll','frame_num','dl_orig','dl_georef','dl_index','geometry'])
    src_srs = "EPSG:3857"
    no_roll_agencies = ['AMS', 'USGS']
    # file shapefile data container
    for key in cog_keys:
        print(key)

        fly = key.split('/')[-4]
        if "_" in fly:
            agency = fly.split("_")[0]
        else:
            agency = ''

        location = key
        dl_orig = key.replace('/vsis3/', 'https://s3.amazonaws.com/').replace('cog/', 'scanned/')
        dl_georef = key.replace('/vsis3/', 'https://s3.amazonaws.com/')
        dl_index = 'https://s3.amazonaws.com/' + source_bucket + '/' + shp_key + '_idx.zip'

        frame_name = key.split('/')[-1].replace('.tif','')
        if 'mosaic' not in frame_name and '/mosaic/' not in key and '/index/' not in key and '/StratMap/' not in key:
            date = frame_name.split('_')[0]
            if "-" in frame_name.split('_')[1]:
                roll = frame_name.split('_')[1].split('-')[0]
                frame_num = frame_name.split('_')[1].split('-')[1]
            else:
                if agency in no_roll_agencies:
                    roll = "N/A"
                    frame_num = frame_name.split('_')[1]
                else:
                    print(no_roll_agencies)
                    print(key)
                    raise ValueError('no roll in filename and agency not in no_roll_agencies')
        elif 'mosaic' not in frame_name and '/mosaic/' not in key and '/index/' in key and '/StratMap/' not in key:
            roll = frame_name.split('_')[0]
            date = frame_name.split('_')[1]
            frame_num = frame_name.split('_')[2]
        elif 'mosaic' in frame_name and '/mosaic/' in key and '/index/' not in key and '/StratMap/' not in key:
            date = 'MULTIPLE'
            roll = 'MULTIPLE'
            frame_num = frame_name.replace("mosaic", "")
        elif '/StratMap/' in key:
            date = frame_name.split('_')[2]
            roll = frame_name.split('_')[0]
            frame_num = frame_name.split('_')[1]

        gdal.VSICurlClearCache()
        dataset = gdal.Open(key)
        ulx, xres, xskew, uly, yskew, yres  = dataset.GetGeoTransform()
        lrx = ulx + (dataset.RasterXSize * xres)
        lry = uly + (dataset.RasterYSize * yres)
        print(ulx, uly, lrx, lry)
        bounds = [ulx, lry, lrx, uly]
        df = df.append({'location':location, 'src_srs': src_srs, 'date': date, 'roll': roll, 'frame_num': frame_num, 'dl_orig': dl_orig, 'dl_georef': dl_georef, 'dl_index': dl_index, 'geometry': box(bounds[0], bounds[1], bounds[2], bounds[3])},ignore_index=True)

    # create shapefile for s3
    df.to_file("/tmp/tile_index.shp")
    # create tile index zipfile
    zipper = '/tmp/%s.zip' % (index_name + '_idx')
    z = zipfile.ZipFile(zipper, mode='w')

    # upload shapefile to s3 and build zipfile
    shp_suffixes = ['.cpg', '.dbf', '.shp', '.shx']
    for sfx in shp_suffixes:
        filename = '/tmp/tile_index' + sfx
        keyname = shp_key + sfx
        print('uploading: ' + keyname)
        client.upload_file(filename, source_bucket, keyname, ExtraArgs={'ACL':'public-read'})
        z.write(filename, filename.replace('/tmp/', ''))
    print("shapefile upload success!")

    # upload ZipFile
    z.close()
    keyname = key_path + "tile_index/" + index_name + '_idx.zip'
    client.upload_file(zipper, source_bucket, keyname, ExtraArgs={'ACL':'public-read'})
    print('zipfile upload success!')

    # upload geodataframe to postgis
    df['geom'] = df['geometry'].apply(lambda x: WKTElement(x.wkt, srid=3857))
    df.drop('geometry', 1, inplace=True)
    print('geom reformatted')
    table_name = index_name.lower()
    print(table_name)
    df.to_sql(table_name, engine, if_exists='replace', index=True, index_label='oid', dtype={'geom': Geometry('POLYGON', srid=3857)})
    print('tile index added to postgis!')

    # cleanup /tmp
    for sfx in shp_suffixes:
        filename = '/tmp/tile_index' + sfx
        os.remove(filename)
    os.remove(zipper)
    print('/tmp cleaned up.')

    gdal.VSICurlClearCache()

if __name__ == '__main__':
    lambda_handler(event='event', context='context')
