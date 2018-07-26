# --------------- IMPORTS ---------------
import os
import boto3
import json
import gdal

georef_sub_dir = os.environ.get('georefSubDir')
epsg_sub_dir = os.environ.get('epsgSubDir')

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

    # update ACL for uploaded /scanned tif
    # /scanned tif only exists for frames and indexes - NOT mosaics
    if '/frames/scanned/' in source_key or '/index/scanned/' in source_key:
        print('updating scanned/ tif ACL to public-read')
        print(source_key)
        client = boto3.client('s3')
        response = client.put_object_acl(ACL='public_read',Bucket=source_bucket,Key=source_key)
        print(response)
        gdal.VSICurlClearCache()
        return

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
    # verify not a temp tif in epsg3857 directory
    elif epsg_sub_dir in source_key:
        print("error: key includes the 'epsgSubDir' env variable. exiting...")
        print(source_key)
        return
    else:
        dst_crs = 'EPSG:3857'
        prefix = '/vsis3/' + source_bucket + '/'
        s3_path = prefix + source_key
        epsg_folder = 'georef/' + epsg_sub_dir
        upload_key = source_key.replace('georef/', epsg_folder).replace('TIF', 'tif')
        gdal.VSICurlClearCache()
        try:
            epsg = int(gdal.Info(s3_path, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
            print(epsg)
        except Exception as e:
            print(e)
            print("no epsg. uh oh... this raster is probably georeferenced but wasn't exported to GeoTiff")
            epsg = ''

        if epsg != 3857:
            print("let's reproject...")
            reprojected_tif = '/tmp/reprojected.tif'
            try:
                gdal.Warp(reprojected_tif,s3_path,dstSRS=dst_crs)
            except Exception as e:
                print(e)
            # connect to s3
            client = boto3.client('s3')
            print('uploading reprojected tif')
            client.upload_file(reprojected_tif, source_bucket, upload_key)
            gdal.VSICurlClearCache()
            # cleanup /tmp
            print('cleaning up /tmp')
            os.remove(reprojected_tif)

        else:
            print("already EPSG 3857; nothing to do here.")

        print('invoking ls4-01-compress')
        client = boto3.client('lambda')
        payload = {'sourceBucket': source_bucket, 'sourceKey': upload_key}
        response = client.invoke(
            FunctionName='ls4-01-compress',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        print(response)
    print("that's all folks!!")


if __name__ == '__main__':
    lambda_handler(event='event', context='context')
