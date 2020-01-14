import boto3
# import requests
# import json

client = boto3.client('s3')
ls4_bucket = 'tnris-ls4'
q_bucket = 'tnris-public-data'


if q_bucket != '' and ls4_bucket != '':
    ls4_tifs = []
    ls4_deets = []
    q_tifs = []
    q_deets = []

    def ls4_run(ct=None, loop=0):
        print('loop: ' + str(loop))
        if ct is None:
            response = client.list_objects_v2(
                Bucket=ls4_bucket,
                Prefix='bw/'
            )
        else:
            response = client.list_objects_v2(
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
                ls4_deets.append([county, agency, year, sheet])
                # print(county, agency, year, sheet)
            if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                    print('what the TIF???' + c['Key'])
                
        loop += 1
        if response['IsTruncated'] is True:
            ls4_run(response['NextContinuationToken'], loop)
        else:
            print('index scans .tif key count: ' + str(len(ls4_tifs)))
            return 

    def q_run(ct=None, loop=0):
        print('loop: ' + str(loop))
        if ct is None:
            response = client.list_objects_v2(
                Bucket=q_bucket,
                Prefix='prod-historic/Historic_Images/'
            )
        else:
            response = client.list_objects_v2(
                Bucket=q_bucket,
                Prefix='prod-historic/Historic_Images/',
                ContinuationToken=ct
            )
        for c in response['Contents']:
            if '/Index/' in c['Key']:
                # find all tifs that are not in the MultiCounty subdirectory
                # and are not AMS (since AMS are mainly line indexes)
                # and are not line indexes (LI) at all
                if (
                    c['Key'][-4:] == '.tif'
                    or c['Key'][-4:] == '.TIF'
                    ) and 'MultiCounty' not in c['Key'] and 'AMS' not in c['Key'] and '_LI_' not in c['Key']:
                    q_tifs.append(c['Key'])
                    try:
                        county = c['Key'].split('/')[2]
                        filename = c['Key'].split('/')[-1].replace('.tif', '').replace('.TIF', '')
                        agency = filename.split('_')[0]
                        year = filename.split('_')[1]
                        sheet = filename.split('_')[2]
                        q_deets.append([county, agency, year, sheet])
                        # print(county, agency, year, sheet)
                    except:
                        print('issue getting county, agency, year, & sheet:' + c['Key'])
                if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                    print('what the TIF???' + c['Key'])
                
        loop += 1
        if response['IsTruncated'] is True:
            q_run(response['NextContinuationToken'], loop)
        else:
            print('index file .tif key count: ' + str(len(q_tifs)))
            return 

    print('compiling LS4 drive contents...')
    ls4_run()
    print('compiling Q drive contents...')
    q_run()
    
    print('totals---')
    print('ls4: %s --- q: %s' % (str(len(ls4_tifs)), str(len(q_tifs))))

    print('time to compare....')
    print('ls4 tifs not in Q drive:')
    count = 0
    for l in ls4_deets:
        if l not in q_deets:
            count += 1
            print(l)
    print('%s total ls4 tifs not in Q drive.' % str(count))
    print('q tifs not in ls4:')
    count = 0
    for q in q_deets:
        if q not in ls4_deets:
            count += 1
            print(q)
    print('%s q tifs not in ls4.' % str(count))

else:
    print('buckets not declared. populate variables and try again.')


print("that's all folks!!")