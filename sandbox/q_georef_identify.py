import boto3

client = boto3.client('s3')
ls4_bucket = 'tnris-ls4'
q_bucket = 'tnris-public-data'


if q_bucket != '' and ls4_bucket != '':
    ls4_tifs = []
    ls4_deets = []
    q_index_keys = []
    q_tifs = []
    coll_list = []

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
                    ls4_deets.append([county, agency, year, sheet, dpi])
                except:
                    ls4_deets.append([county, agency, year, sheet])
                if [county, agency, year] not in coll_list:
                    coll_list.append([county, agency, year])
                # print(county, agency, year, sheet)
            if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
                print('what the TIF???' + c['Key'])
            # if 'USAF' in c['Key']:
            #     print('USAF Ugh: '+ c['Key'])
                
        loop += 1
        if response['IsTruncated'] is True:
            ls4_run(response['NextContinuationToken'], loop)
        else:
            print('index scans .tif key count: ' + str(len(ls4_tifs)))
            return 

    # def q_run(ct=None, loop=0):
    #     print('loop: ' + str(loop))
    #     if ct is None:
    #         response = client.list_objects_v2(
    #             Bucket=q_bucket,
    #             Prefix='prod-historic/Historic_Images/'
    #         )
    #     else:
    #         response = client.list_objects_v2(
    #             Bucket=q_bucket,
    #             Prefix='prod-historic/Historic_Images/',
    #             ContinuationToken=ct
    #         )
    #     for c in response['Contents']:
    #         if '/Index/' in c['Key']:
    #             # find all tifs that are not in the MultiCounty subdirectory
    #             # and are not AMS (since AMS are mainly line indexes)
    #             # and are not USAF (since USAF are special cases)
    #             # and are not line indexes (LI) at all
    #             q_index_keys.append(c['Key'])
    #             if (
    #                 c['Key'][-4:] == '.tif'
    #                 or c['Key'][-4:] == '.TIF'
    #                 ) and 'MultiCounty' not in c['Key'] and 'AMS' not in c['Key'] and 'USAF' not in c['Key'] and '_LI_' not in c['Key']:
    #                 q_tifs.append(c['Key'])
    #             if c['Key'][-4:] == '.TIF' or c['Key'][-4:] == '.TIFF' or c['Key'][-4:] == '.tiff':
    #                 print('what the TIF???' + c['Key'])
    #             # if 'USAF' in c['Key']:
    #             #     print('USAF Ugh: '+ c['Key'])
                
    #     loop += 1
    #     if response['IsTruncated'] is True:
    #         q_run(response['NextContinuationToken'], loop)
    #     else:
    #         print('index file .tif key count: ' + str(len(q_tifs)))
    #         return 

    print('compiling LS4 drive contents...')
    ls4_run()
    # print('compiling Q drive contents...')
    # q_run()
    
    print('totals---')
    print('ls4: %s --- q: %s' % (str(len(ls4_tifs)), str(len(q_tifs))))

    print('time to compare....')
    # wf = []
    # af = []
    # ov = []
    # counter = 1
    # for t in q_tifs:
    #     # print('%s/%s' % (str(counter), str(len(q_tifs))))
    #     worldfile = t.replace('.tif', '.tfwx')
    #     tfw = t.replace('.tif', '.tfw')
    #     if worldfile not in q_index_keys and tfw not in q_index_keys:
    #         # print('missing worldfile: ' + t)
    #         wf.append(t)
        
    #     auxfile = t + '.aux.xml'
    #     if auxfile not in q_index_keys:
    #         # print('missing auxfile: ' + t)
    #         af.append(t)

    #     overviews = t + '.ovr'
    #     if overviews not in q_index_keys:
    #         # print('missing overviews: ' + t)
    #         ov.append(t)

    #     counter += 1
    # print('missing Q georef totals---')
    # print('worldfiles/auxfiles/overviews')
    # print('%s/%s/%s' % (str(len(wf)), str(len(af)), str(len(ov))))
    
    ls4_not_georef = []
    wf = []
    af = []
    ov = []
    counter = 1
    for idx, d in enumerate(coll_list):
        print(d, idx, counter)
        # print('%s/%s' % (str(counter), str(len(ls4_deets))))
        # try:
        #     keypath = 'prod-historic/Historic_Images/%s/Index/%s_%s_%s_%s.tif' % (d[0], d[1], d[2], d[3], d[4])
        # except:
        #     keypath = 'prod-historic/Historic_Images/%s/Index/%s_%s_%s.tif' % (d[0], d[1], d[2], d[3])
        
        # flag = False
        # if keypath not in q_index_keys:
        #     flag = True
        #     print('missing tif keypath: ' + keypath)

        # worldfile = keypath.replace('.tif', '.tfwx')
        # tfw = keypath.replace('.tif', '.tfw')
        # if worldfile not in q_index_keys:
        #     if tfw not in q_index_keys:
        #         print('missing worldfile: ' + tfw)
        #         wf.append(keypath)
        #         flag = True
        # else:
        #     auxfile = keypath + '.aux.xml'
        #     if auxfile not in q_index_keys:
        #         print('missing auxfile: ' + auxfile)
        #         af.append(keypath)
        #         flag = True

        # overviews = keypath + '.ovr'
        # if overviews not in q_index_keys:
        #     print('missing overviews: ' + overviews)
        #     ov.append(keypath)
        #     flag = True

        # if flag:
        #     ls4_not_georef.append(d)

        counter += 1
    # print('LS4 keys missing Q georef totals---')
    # print('worldfiles/auxfiles/overviews')
    # print('%s/%s/%s' % (str(len(wf)), str(len(af)), str(len(ov))))
    # print('ls4 scanned indexes missing 1(or more) georeference files in q---')
    # print('total count: %s' % str(len(ls4_not_georef)))
    # for l in ls4_not_georef:
    #     print(l)
    print('total', str(len(coll_list)))

else:
    print('bucket not declared. populate variables and try again.')


print("that's all folks!!")