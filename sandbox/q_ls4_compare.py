import boto3
# import requests
# import json

client = boto3.client('s3')
ls4_bucket = 'tnris-ls4'
q_bucket = 'tnris-public-data'


if q_bucket != '' and ls4_bucket != '':
    ls4_tifs = []
    q_tifs = []

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
            if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                    print(c['Key'])
                
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
                if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                    print(c['Key'])
                
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

else:
    print('buckets not declared. populate variables and try again.')


print("that's all folks!!")