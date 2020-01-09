import boto3
import gdal
import requests
import json

client = boto3.client('s3')
bucket = 'tnris-public-data'


colls = requests.get("https://api.tnris.org/api/v1/historical/collections")
all_colls = colls.json()['results']
more_colls = requests.get("https://api.tnris.org/api/v1/historical/collections?limit=1000&offset=1000")
all_colls.extend(more_colls.json()['results'])
print('total lore public collection count: ' + str(len(all_colls)))
# lore = []
# for c in all_colls:
#     if c['index_service_url'] is not None:
#         links = json.loads("[%s]" % c['scanned_index_ls4_links'])
#         for l in links:
#             dl = l['link'].replace("https://s3.amazonaws.com/tnris-ls4/","").replace("https://tnris-ls4.s3.amazonaws.com/","")
#             lore.append(dl)
#             # print(dl)
# print('total lore scanned index ls4 links count: ' + str(len(lore)))

if bucket != '':
    contents = []
    tifs = []

    def run(ct=None, loop=0):
        print('loop: ' + str(loop))
        if ct is None:
            response = client.list_objects_v2(
                Bucket=bucket,
                Prefix='prod-historic/Historic_Images/'
            )
        else:
            response = client.list_objects_v2(
                Bucket=bucket,
                Prefix='prod-historic/Historic_Images/',
                ContinuationToken=ct
            )
        for c in response['Contents']:
            if '/Index/' in c['Key']:
                contents.append(c['Key'])
                # find all tifs that are not in the MultiCounty subdirectory
                # and are not AMS (since AMS are mainly line indexes)
                # and are not line indexes (LI) at all
                if (
                    c['Key'][-4:] == '.tif'
                    or c['Key'][-4:] == '.TIF'
                    ) and 'MultiCounty' not in c['Key'] and 'AMS' not in c['Key'] and '_LI_' not in c['Key']:
                    tifs.append(c['Key'])
                if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                    print(c['Key'])
                
        loop += 1
        if response['IsTruncated'] is True:
            run(response['NextContinuationToken'], loop)
        else:
            print('contents compiled. index files key count: ' + str(len(contents)))
            print('index file .tif key count: ' + str(len(tifs)))
            return 

    print('compiling contents...')
    run()

    # print('epsg check...')
    # for key in tifs:
    #     s3_path = '/vsis3/' + bucket + '/' + key
    #     try:
    #         epsg = int(gdal.Info(s3_path, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
    #         print(epsg)
    #     except:
    #         print('bad epsg --' + gdal.Info(s3_path, format='json')['coordinateSystem']['wkt'] + '-- ' + key)

else:
    print('no bucket declared. populate variable and try again.')


print("that's all folks!!")