import boto3

client = boto3.client('s3')
ls4_bucket = 'tnris-ls4'
q_bucket = 'tnris-public-data'


if q_bucket != '' and ls4_bucket != '':
    ls4_tifs = []
    ls4_deets = []

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

    print('compiling LS4 drive contents...')
    ls4_run()
    
    print('totals---')
    print('ls4 tifs: %s' % (str(len(ls4_tifs))))
    print('ls4 deets: %s' % (str(len(ls4_deets))))

    print('time to process....')
    total = str(len(ls4_deets))
    counter = 1
    for d in ls4_deets:
        print('%s/%s' % (str(counter), total))
        tif = 'prod-historic/Historic_Images/%s/Index/%s_%s_%s.tif' % (d[0], d[1], d[2], d[3])
        worldfile = tif.replace('.tif', '.tfwx')
        auxfile = tif + '.aux.xml'
        overviews = tif + '.ovr'

        counter += 1

else:
    print('bucket not declared. populate variables and try again.')


print("that's all folks!!")