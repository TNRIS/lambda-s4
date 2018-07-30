# --------------- IMPORTS ---------------
import os
import boto3
import json
import gdal

georef_sub_dir = os.environ.get('georefSubDir')
epsg_sub_dir = os.environ.get('epsgSubDir')
aws_account = os.environ.get('AWS_ACCOUNT_ID')
sns_error_topic = os.environ.get('SNS_ERROR_TOPIC')

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

        # connect to s3
        client = boto3.client('s3')
        if epsg != 3857:
            print("let's reproject...")
            reprojected_tif = '/tmp/reprojected.tif'
            try:
                gdal.Warp(reprojected_tif,s3_path,dstSRS=dst_crs)
            except Exception as e:
                print(e)

            print('uploading reprojected tif')
            client.upload_file(reprojected_tif, source_bucket, upload_key)
            gdal.VSICurlClearCache()
            # cleanup /tmp
            print('cleaning up /tmp')
            os.remove(reprojected_tif)

        else:
            print("already EPSG 3857; copying to epsg folder.")
            client.copy({'Bucket': source_bucket, 'Key': source_key}, source_bucket, upload_key)

        print('invoking ls4-01-compress')
        client = boto3.client('lambda')
        payload = {'sourceBucket': source_bucket, 'sourceKey': upload_key}
        response = client.invoke(
            FunctionName='ls4-01-compress',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        print(response)

        # check if original exists in /scanned
        client = boto3.client('s3')
        # /scanned tif only exists for frames and indexes - NOT mosaics
        if '/frames/georef/' in source_key or '/index/georef/' in source_key:
            orig = source_key.replace('georef/', 'scanned/')
            # original index uploads don't include tiled number
            if '/index/' in orig:
                tile_num = orig.split('/')[-1].split('_')[-1]
                sfx = tile_num.split('.')[-1]
                orig = orig.replace('_' + tile_num, '.' + sfx)
            try:
                r = client.head_object(Bucket=source_bucket, Key=orig)
                print('original exists at %s' % orig)
            except Exception as e:
                print(e)
                # try alternative extension
                try:
                    if '.tif' in orig:
                        alt = orig.replace('.tif', '.TIF')
                    elif '.TIF' in orig:
                        alt = orig.replace('.TIF', '.tif')
                    else:
                        raise Exception('no tif or TIF extension!')
                    r = client.head_object(Bucket=source_bucket, Key=alt)
                    print('original exists at %s' % alt)
                except Exception as e:
                    print(e)
                    # publish message to the project SNS topic
                    sns = boto3.resource('sns')
                    arn = 'arn:aws:sns:us-east-1:%s:%s' % (aws_account, sns_error_topic)
                    topic = sns.Topic(arn)
                    m = ("GeoTiff uploaded at '%s' in the LS4 bucket is missing "
                         "it's original in the relative /scanned folder. Expected "
                         "it to exist at '%s'. Please upload it now while you're "
                         "doing LS4y stuffs. Might as well... ya know? Thanks "
                         "friend!" % (source_key, orig)
                        )
                    response = topic.publish(
                        Message=m,
                        Subject='LS4 Notification'
                    )
                    print('original /scanned not in s3. sns error message dispatched.')

    print("that's all folks!!")


if __name__ == '__main__':
    lambda_handler(event='event', context='context')
