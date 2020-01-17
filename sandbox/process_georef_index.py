import boto3
import os
import arcpy

client = boto3.client('s3')
ls4_bucket = 'tnris-ls4'
q_bucket = 'tnris-public-data'
working_dir = '<local working directory>'

# to do: turn off ls4 lambdas for running this bulk process

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
        # to do: disable while counter from testing
        while counter == 1:
            print('%s/%s' % (str(counter), total))
            print('clearing working dir...')
            for f in os.listdir(working_dir):
                os.remove(os.path.join(working_dir, f))
            filename_base = '%s_%s_%s' % (d[1], d[2], d[3])

            print('downloading tif...')
            tif = 'prod-historic/Historic_Images/%s/Index/%s.tif' % (d[0], filename_base)
            client.download_file(q_bucket, tif, working_dir + filename_base + '.tif')

            print('downloading worldfile...')
            worldfile = 'prod-historic/Historic_Images/%s/Index/%s.tfwx' % (d[0], filename_base)
            client.download_file(q_bucket, worldfile, working_dir + filename_base + '.tfwx')

            print('downloading auxfile...')
            auxfile = 'prod-historic/Historic_Images/%s/Index/%s.tif.aux.xml' % (d[0], filename_base)
            client.download_file(q_bucket, auxfile, working_dir + filename_base + '.tif.aux.xml')

            print('downloading overviews...')
            overviews = 'prod-historic/Historic_Images/%s/Index/%s.tif.ovr' % (d[0], filename_base)
            client.download_file(q_bucket, overviews, working_dir + filename_base + '.tif.ovr')

            print('check projection...')
            sr = arcpy.Describe(working_dir + filename_base + '.tif').spatialReference
            print(sr.factoryCode, sr.name)
            # to do: handle reprojection of non-3857 rasters
            if sr.factoryCode == 3857:
                print('running CopyRaster for conversion...')
                cog = working_dir + 'out_cog' + filename_base + '.tif'
                try:
                    arcpy.CopyRaster_management(working_dir + filename_base + '.tif', cog,
                                                nodata_value='256', format='COG', transform=True)
                    print('uploading converted COG...')
                    client.upload_file(cog, q_bucket, filename_base + '.tif')
                    # to do: build bounding box shapefile, upload, create service with mapfile and dbase record
                except:
                    print arcpy.GetMessages()

            print('SUCCESS:', q_bucket, tif, working_dir + filename_base + '.tif')
            counter += 1

else:
    print('bucket not declared. populate variables and try again.')


print("that's all folks!!")