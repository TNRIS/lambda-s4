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
    for key in contents:
        filename = key.replace('mapfiles/', '')
        client.download_file(bucket, key, '<pathhh>/mapfile_backup_1/' + filename)

    total = str(len(contents))
    counter = 1
    for key in contents:
        print('%s/%s' % (str(counter), total))
        for f in os.listdir('./mvt'):
                os.remove('./mvt/' + f)
        print(key)
        # filename = key.replace('mapfiles/', '')
        # print(filename)
        # client.download_file(bucket, key, './mvt/' + filename)
        # client.download_file(bucket, key, '<pathhh>/mapfile_backup/' + filename)
        # # with open('./mvt/' + filename) as template:
        # #     t = template.read()
        # f = open('./mvt/' + filename, 'r')
        # t = f.readlines()
        # f.close()
        # print('template opened')
        # # write new mapfile in /tmp
        # mapfile = filename.replace('.map', '_mvt.map')
        # print('writing %s' % mapfile)
        # t.insert(14, "      WMS_SRS 'epsg:3857 epsg:900913'\n")
        # t.insert(20, "  OUTPUTFORMAT\n")
        # t.insert(21, '    NAME "png8"\n')
        # t.insert(22, '    DRIVER AGG/PNG8\n')
        # t.insert(23, '    MIMETYPE "image/png; mode=8bit"\n')
        # t.insert(24, '    IMAGEMODE RGB\n')
        # t.insert(25, '    EXTENSION "png"\n')
        # t.insert(26, '    FORMATOPTION "QUANTIZE_FORCE=on"\n')
        # t.insert(27, '    FORMATOPTION "QUANTIZE_COLORS=256"\n')
        # t.insert(28, '    FORMATOPTION "GAMMA=0.75"\n')
        # t.insert(29, '    TRANSPARENT ON\n')
        # t.insert(30, '  END\n')
        # t.insert(31, '  OUTPUTFORMAT\n')
        # t.insert(32, '    NAME "mvt"\n')
        # t.insert(33, '    DRIVER MVT\n')
        # t.insert(34, '    #FORMATOPTION "EXTENT=512" # default is 4096\n')
        # t.insert(35, '    FORMATOPTION "EDGE_BUFFER=20"\n')
        # t.insert(36, '  END\n')
        # t.insert(50, "      WMS_SRS 'epsg:3857 epsg:900913'\n")
        # t.pop(54)
        # t.insert(68, "        WMS_SRS 'epsg:3857 epsg:900913'\n")
        # f = open('./mvt/' + mapfile, 'w')
        # file_fill = "".join(t)
        # f.write(file_fill)
        # f.close()
        # print('mapfile written')
        # # connect to s3 and upload mapfile
        # s3 = boto3.resource('s3')
        # s3.Bucket(bucket).upload_file('./mvt/' + mapfile,key,ExtraArgs={'Metadata':{'mode':'33204','uid':'500','gid':'500','mtime':'1528814551'}})
        # print("upload success!")
        counter += 1

else:
    print('no bucket declared. populate variable and try again.')


print("that's all folks!!")