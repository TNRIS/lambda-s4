import boto3
from botocore.errorfactory import ClientError
import os
import requests
import json
from operator import itemgetter

client_s3 = boto3.client('s3')
client_lambda = boto3.client('lambda')
ls4_bucket = 'tnris-ls4'
q_bucket = 'tnris-public-data'
working_dir = '<local working directory>'

if q_bucket != '' and ls4_bucket != '':
    ls4_tifs = []
    ls4_deets = []

    def ls4_run(ct=None, loop=0):
        print('loop: ' + str(loop))
        if ct is None:
            response = client_s3.list_objects_v2(
                Bucket=ls4_bucket,
                Prefix='bw/'
            )
        else:
            response = client_s3.list_objects_v2(
                Bucket=ls4_bucket,
                Prefix='bw/',
                ContinuationToken=ct
            )
        for c in response['Contents']:
            # ignore USAF!
            if '/index/scanned/' in c['Key'] and 'USAF' not in c['Key'] and (
                    c['Key'][-4:] == '.tif' or
                    c['Key'][-4:] == '.TIF'):
                ls4_tifs.append(c['Key'])

                county = c['Key'].split('/')[1]
                filename = c['Key'].split('/')[-1].replace('.tif', '').replace('.TIF', '')
                agency = filename.split('_')[0]
                year = filename.split('_')[1]
                sheet = filename.split('_')[2]
                try:
                    dpi = filename.split('_')[3]
                    ls4_deets.append([county, agency, year, sheet, c['Key'], dpi])
                except:
                    ls4_deets.append([county, agency, year, sheet, c['Key']])
                # print(county, agency, year, sheet, c['Key'])
            if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                    print('what the TIF???' + c['Key'])
            # if 'USAF' in c['Key']:
            #     print('USAF Ugh:', c['Key'])

        loop += 1
        if response['IsTruncated'] is True:
            ls4_run(response['NextContinuationToken'], loop)
        else:
            print('index scans .tif key count: ' + str(len(ls4_tifs)))
            return

    print('compiling LS4 drive contents...')
    ls4_run()

    print('totals---')
    print('ls4 tifs: %s' % (str(len(ls4_tifs))))
    print('ls4 deets: %s' % (str(len(ls4_deets))))

    print('using api to pull all mapserver services created...')
    mapserver_string = "https://api.tnris.org/api/v1/historical/mapserver"
    ms_res = requests.get(mapserver_string).json()
    ms_dict = {}
    for m in ms_res:
        ms_dict[m['name']] = m['wms']
    print('%s total mapserver services exist.' % str(len(ms_res)))

    print('time to review....')
    total = str(len(ls4_deets))
    counter = 1
    errors = []
    cog_ugh = []
    api_ugh = []
    multi_ugh = []
    multi_colls = []
    for idx, d in enumerate(ls4_deets):
        print('%s/%s' % (str(counter), total))
        filename_base = '%s_%s_%s' % (d[1], d[2], d[3])
        upload_base = filename_base
        if len(d) == 6:
            filename_base = '%s_%s_%s_%s' % (d[1], d[2], d[3], d[5])
        # tif = 'prod-historic/Historic_Images/%s/Index/%s.tif' % (d[0], filename_base)

        # use idx >= 0 to process entire list. otherwise, declare
        # index location to start in the middle of the process
        # if idx <= 5305:
        try:
            # print('checking for uploaded COG...')
            upload_key = 'bw/%s/%s_%s/index/cog/%s.tif' % (d[0], d[1], d[2], upload_base)
            try:
                client_s3.head_object(Bucket=ls4_bucket, Key=upload_key)
            except:
                print(d, 'bad cog')
                errors.append([d, 'bad cog'])
                if d not in cog_ugh:
                    cog_ugh.append(d)

            # print('checking for processed tile index zipfile...')
            upload_shp_zip = "%s_%s_%s_index_idx.zip" % (d[0], d[1], d[2])
            upload_key = 'bw/%s/%s_%s/index/cog/tile_index/%s' % (d[0], d[1], d[2], upload_shp_zip)
            try:
                client_s3.head_object(Bucket=ls4_bucket, Key=upload_key)
            except:
                print(d, 'bad zipfile')
                errors.append([d, 'bad zipfile'])

            # print('checking for generated mapfile...')
            mapfile_key = 'mapfiles/%s_%s_%s_index.map' % (d[0].lower(), d[1].lower(), d[2])
            try:
                client_s3.head_object(Bucket=ls4_bucket, Key=mapfile_key)
            except:
                print(d, 'bad mapfile')
                errors.append([d, 'no mapfile'])

            # print('using api to find collection_id...')
            url_string = "https://api.tnris.org/api/v1/historical/collections?scanned_index_ls4_links__icontains=s3.amazonaws.com/tnris-ls4/%s" % (d[4])
            # print(url_string)
            api_res = requests.get(url_string).json()['results']
            if len(api_res) != 1:
                print(url_string)
                print('%s collections contain the same scanned index ls4 link url' % str(len(api_res)))
                print(api_res)
                errors.append([d, 'api coll id'])
                if d not in api_ugh:
                    api_ugh.append(d)
            collection_id = api_res[0]['collection_id']
            index_service_url = api_res[0]['index_service_url']
            # print(index_service_url)
            if index_service_url != ("http://mapserver.tnris.org/wms/?map=/" + mapfile_key):
                print(d, 'bad mapfile in database!!!', index_service_url)
                errors.append([d, 'bad index service url'])
                if d not in multi_ugh:
                    multi_ugh.append(d)
                multi_coll = [collection_id, d[1], d[2]]
                if multi_coll not in multi_colls:
                    multi_colls.append(multi_coll)

            # print('verifying creation of mapserver service...')
            service_name = '%s_%s_%s_index' % (d[0].lower(), d[1].lower(), d[2])
            if service_name not in ms_dict.keys():
                print(d, 'service name does not exist!', service_name)
                errors.append([d, 'service name does not exit'])
            else:
                if ms_dict[service_name] != index_service_url:
                    print(d, 'mapserver service not equal to lore collection index_service_url')
                    print(ms_dict[service_name])
                    print(index_service_url)
                    errors.append([d, 'mapfile vs service name'])

        except Exception as e:
            print('__error__', e)
            errors.append([d, 'major e'])

        counter += 1

    print('ERRORS---')
    for e in errors:
        print(e)
    print('total', len(errors))

    print('cog processing errors---')
    for e in cog_ugh:
        print(e)
    print('total', len(cog_ugh))

    print('api procssing errors---')
    for e in api_ugh:
        print(e)
    print('total', len(api_ugh))

    print('multi processing errors---')
    for e in multi_ugh:
        print(e)
    print('total', len(multi_ugh))

    print('multi processing errors collection ids:')
    for e in sorted(multi_colls, key=itemgetter(0)):
        print(e)

    print('cog errors as array for copy/paste:')
    print(cog_ugh)

else:
    print('bucket not declared. populate variables and try again.')

print("that's all folks!!")