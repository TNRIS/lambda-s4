import boto3
import gdal
import requests
import json

client = boto3.client('s3')
bucket = 'tnris-ls4'
contents = []

colls = requests.get("https://api.tnris.org/api/v1/historical/collections")
all_colls = colls.json()['results']
more_colls = requests.get("https://api.tnris.org/api/v1/historical/collections?limit=1000&offset=1000")
all_colls.extend(more_colls.json()['results'])
print('total lore public collection count: ' + str(len(all_colls)))
lore = []
for c in all_colls:
    if c['scanned_index_ls4_links'] != "":
        links = json.loads("[%s]" % c['scanned_index_ls4_links'])
        for l in links:
            dl = l['link'].replace("https://s3.amazonaws.com/tnris-ls4/","").replace("https://tnris-ls4.s3.amazonaws.com/","")
            lore.append(dl)
            # print(dl)
print('total lore scanned index ls4 links count: ' + str(len(lore)))

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
    index_scanned = []
    all_georef = []
    bad_epsg = []
    not_in_public_lore = []
    print("not in public Lore, but in s3:")
    for k in contents:
        key = k['Key']
        if '/index/scanned/' in key and key[-1] != '/':
            index_scanned.append(key)
            if key not in lore:
                print(key)
                not_in_public_lore.append(key)
            client = boto3.client('s3')
            # response = client.put_object_acl(ACL='public-read',Bucket=bucket,Key=key)
            # print(key)
        if (
            '/georef' in key
            and key[-1] != '/'
            ):
            all_georef.append(key)
            s3_path = '/vsis3/' + bucket + '/' + key
            epsg = int(gdal.Info(s3_path, format='json')['coordinateSystem']['wkt'].rsplit('"EPSG","', 1)[-1].split('"')[0])
            print('oops, bad georef epsg: ' + key + '---' + epsg)

    print('indexes-----')
    print('s3 count scanned: ' + str(len(index_scanned)))
    print('total count in s3 but not in public lore: ' + str(len(not_in_public_lore)))
    missing = len(index_scanned) - (len(lore) + len(not_in_public_lore))
    print('missing: ' + str(missing))
    print('georef s3-----')
    print('s3 count georef: ' + str(len(all_georef)))

    bad_epsg = []
    print("bad epsg for key in s3:")
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
                print("issue getting epsg for:" + key)

    print('georef s3-----')
    print('total count s3 bad epsg: ' + str(len(bad_epsg)))

    not_in_s3 = []
    print('not in s3, but in public lore scanned index ls4 links:')
    for l in lore:
        if l not in index_scanned:
            print(l)
            not_in_s3.append(l)
    print('-----')
    print('total count lore scanned index ls4 links : ' + str(len(lore)))
    print('total count lore scanned index ls4 links not in s3: ' + str(len(not_in_s3)))

else:
    print('no bucket declared. populate variable and try again.')


print("that's all folks!!")