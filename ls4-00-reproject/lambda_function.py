# --------------- IMPORTS ---------------
import os
import boto3
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import json

georef_sub_dir = os.environ.get('georefSubDir')

# --------------- Main handler ------------------

def lambda_handler(event, context):
    print(event)
    # establish some variables
    
    # prepare input event
    if 'sourceBucket' not in event.keys():
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        source_key = event['Records'][0]['s3']['object']['key']
        print('fired by event!')
        print(source_bucket, source_key)
    else:
        source_bucket = event['sourceBucket']
        source_key = event['sourceKey']

    # verify input is a georef upload
    if 'georef/' not in source_key:
        print("error: key doesn't include '/georef/'. exiting...")
        print(source_key)
        return
    # verify not a temp tif in the georefSubDir
    elif georef_sub_dir in source_key:
        print("error: key includes the 'georefSubDir' env variable. exiting...")
        print(source_key)
        return
    else:
        dst_crs = 'EPSG:3857'
        prefix = 's3://' + source_bucket + '/'
        s3_path = prefix + source_key
        with rasterio.open(s3_path) as src:
            print(src.crs['init'])
            if src.crs['init'] != 'epsg:3857':
                print("let's reproject...")
                transform, width, height = calculate_default_transform(
                    src.crs, dst_crs, src.width, src.height, *src.bounds)
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': dst_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })
                print('transformation variables compiled')
                reprojected_tif = '/tmp/reprojected.tif'
                with rasterio.open(reprojected_tif, 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.nearest)
                    print('reprojected!')
                # connect to s3
                client = boto3.client('s3')
                print('uploading reprojected tif')
                client.upload_file(reprojected_tif, source_bucket, source_key)
                # cleanup /tmp
                print('cleaning up /tmp')
                os.remove(reprojected_tif)

            else:
                print("already EPSG 3857; nothing to do here.")

            print('invoking ls4-01-compress')
            client = boto3.client('lambda')
            payload = {'sourceBucket': source_bucket, 'sourceKey': source_key}
            response = client.invoke(
                FunctionName='ls4-01-compress',
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            print(response)
    print("that's all folks!!")


if __name__ == '__main__':
    lambda_handler(event='event', context='context')
