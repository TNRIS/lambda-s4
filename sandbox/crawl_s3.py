import boto3
import gdal

client = boto3.client('s3')
bucket = ''
contents = []

if bucket != '':

    def run(ct=None, loop=0):
        print('loop: ' + str(loop))
        if ct is None:
            response = client.list_objects_v2(
                Bucket=bucket,
                Prefix='bw/'
            )
        else:
            response = client.list_objects_v2(
                Bucket=bucket,
                Prefix='bw/',
                ContinuationToken=ct
            )
        contents.extend(response['Contents'])
        loop += 1
        if response['IsTruncated'] is True:
            run(response['NextContinuationToken'], loop)
        else:
            print('contents compiled. key count: ' + str(len(contents)))
            return 

    print('compiling contents...')
    run()

    # slim down into needed lists
    # index_scanned = []
    # index_georef = []
    # bad_epsg = []
    # for k in contents:
    #     key = k['Key']
    #     if '/index/scanned/' in key and key[-1] != '/':
    #         index_scanned.append(key)
    #     if (
    #         '/index/georef/' in key
    #         and key[-1] != '/'
    #         and '/Anderson/USDA_1940/' not in key #ignore test coll
    #         ):
    #         index_georef.append(key)
    #         # print(key)
    #         s3_path = '/vsis3/' + bucket + '/' + key
    #         epsg = int(gdal.Info(s3_path, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
    #         print(epsg)

    # print('indexes-----')
    # print('scanned: ' + str(len(index_scanned)))
    # print('georef: ' + str(len(index_georef)))

    bad_epsg = []
    for k in contents:
        key = k['Key']
        if (
            '/georef/' in key
            and key[-1] != '/'
            and '.ovr' not in key
            and '/deflate/' not in key
            and 'tile_index' not in key
            ):
            try:
                s3_path = '/vsis3/' + bucket + '/' + key
                epsg = int(gdal.Info(s3_path, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
                if epsg != 3857:
                    print(epsg, key)
                    bad_epsg.append(key)
            except:
                print(key)

    print('-----')
    print('epsg: ' + str(len(bad_epsg)))
else:
    print('no bucket declared. populate variable and try again.')


print("that's all folks!!")