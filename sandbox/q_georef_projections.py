import boto3
import os
import arcpy
from datetime import datetime

client_s3 = boto3.client('s3')
ls4_bucket = 'tnris-ls4'
q_bucket = 'tnris-public-data'
working_dir = '<local working directory>'

if q_bucket != '' and ls4_bucket != '':
    ls4_tifs = []
    ls4_deets = []
    start_now = datetime.now()
    print('start now', start_now)

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
            if '/index/scanned/' in c['Key'] and (
                    c['Key'][-4:] == '.tif' or
                    c['Key'][-4:] == '.TIF'):
                ls4_tifs.append(c['Key'])

                county = c['Key'].split('/')[1]
                filename = c['Key'].split('/')[-1].replace('.tif', '').replace('.TIF', '')
                agency = filename.split('_')[0]
                year = filename.split('_')[1]
                sheet = filename.split('_')[2]
                ls4_deets.append([county, agency, year, sheet, c['Key']])
                # print(county, agency, year, sheet, c['Key'])
            if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                    print('what the TIF???' + c['Key'])

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

    print('time to sift....')
    total = str(len(ls4_deets))
    counter = 1
    projections = {'errors': 0}
    for d in ls4_deets:
        print('%s/%s' % (str(counter), total))
        print('clearing working dir...')
        for f in os.listdir(working_dir):
            os.remove(os.path.join(working_dir, f))
        filename_base = '%s_%s_%s' % (d[1], d[2], d[3])

        try:
            print('downloading tif...')
            tif = 'prod-historic/Historic_Images/%s/Index/%s.tif' % (d[0], filename_base)
            client_s3.download_file(q_bucket, tif, working_dir + filename_base + '.tif')

            print('downloading worldfile...')
            worldfile = 'prod-historic/Historic_Images/%s/Index/%s.tfwx' % (d[0], filename_base)
            client_s3.download_file(q_bucket, worldfile, working_dir + filename_base + '.tfwx')

            print('downloading auxfile...')
            auxfile = 'prod-historic/Historic_Images/%s/Index/%s.tif.aux.xml' % (d[0], filename_base)
            client_s3.download_file(q_bucket, auxfile, working_dir + filename_base + '.tif.aux.xml')

            print('downloading overviews...')
            overviews = 'prod-historic/Historic_Images/%s/Index/%s.tif.ovr' % (d[0], filename_base)
            client_s3.download_file(q_bucket, overviews, working_dir + filename_base + '.tif.ovr')

            print('check projection...')
            sr = arcpy.Describe(working_dir + filename_base + '.tif').spatialReference
            print(sr.factoryCode, sr.name)
            if sr.factoryCode not in projections.keys():
                projections[sr.factoryCode] = 1
            else:
                projection_count = projections[sr.factoryCode]
                projection_count += 1
                projections[sr.factoryCode] = projection_count
        except:
            error_count = projections['errors']
            error_count += 1
            projections['errors'] = error_count

        counter += 1

    print('FINAL TOTALS---')
    print(projections)
    print('timestamps---')
    print('start', start_now)
    print('end', datetime.now())

else:
    print('bucket not declared. populate variables and try again.')

print("that's all folks!!")