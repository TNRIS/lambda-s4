import boto3, os

client = boto3.client('s3')
bucket = 'tnris-ls4'
contents = []

if bucket != '':

    def run(ct=None, loop=0):
        print('loop: ' + str(loop))
        if ct is None:
            response = client.list_objects_v2(
                Bucket=bucket,
                Prefix='mapfiles/'
            )
        else:
            response = client.list_objects_v2(
                Bucket=bucket,
                Prefix='mapfiles/',
                ContinuationToken=ct
            )

        for c in response['Contents']:
            if c['Key'] != 'mapfiles/':
                contents.append(c['Key'])
        loop += 1
        if response['IsTruncated'] is True:
            run(response['NextContinuationToken'], loop)
        else:
            print('contents compiled. key count: ' + str(len(contents)))
            return 

    print('compiling contents...')
    run()
    print('%s mapfiles found' % str(len(contents)))
    print(contents[0], ' ---> ', contents[-1])

    # download all original mapfiles for backup (although, versioning has been enabled on the bucket)
    # for key in contents:
    #     filename = key.replace('mapfiles/', '')
    #     client.download_file(bucket, key, '<insert local path>/mapfile_backup_1/' + filename)
    for f in os.listdir('./mvt'):
        os.remove('./mvt/' + f)

    total = str(len(contents))
    counter = 1
    for key in contents:
        print('%s/%s' % (str(counter), total))
        # print(key)
        filename = key.replace('mapfiles/', '')
        print(filename)
        client.download_file(bucket, key, './mvt/' + filename)
        # client.download_file(bucket, key, '<insert local path>/mapfile_backup/' + filename)
        with open('./mvt/' + filename) as template:
            t = template.read()
        print('template opened')
        # write new mapfile in /tmp
        mapfile = filename.replace('.map', '_mvt.map')
        print('writing %s' % mapfile)
        t = t.replace("http://mapserver.tnris.org", "https://mapserver.tnris.org")
        f = open('./mvt/' + mapfile, 'w')
        f.write(t)
        f.close()
        print('mapfile written')
        # connect to s3 and upload mapfile
        # s3 = boto3.resource('s3')
        # s3.Bucket(bucket).upload_file('./mvt/' + mapfile,key,ExtraArgs={'Metadata':{'mode':'33204','uid':'500','gid':'500','mtime':'1528814551'}})
        # print("upload success!")
        counter += 1

else:
    print('no bucket declared. populate variable and try again.')


print("that's all folks!!")