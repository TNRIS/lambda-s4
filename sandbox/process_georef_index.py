import boto3
import os
import arcpy
import requests
import json

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
                # TO DO: handle _XXXdpi filenames!!!
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

    print('time to process....')
    total = str(len(ls4_deets))
    counter = 1
    for idx, d in enumerate(ls4_deets):
        # to do: disable while counter from testing
        print('%s/%s' % (str(counter), total))
        if idx == (len(ls4_deets) - 1):
            print('clearing working dir...')
            for f in os.listdir(working_dir):
                os.remove(os.path.join(working_dir, f))
            filename_base = '%s_%s_%s' % (d[1], d[2], d[3])

        # TO DO: handle _XXXdpi filenames!!!
        # TO DO: handle tfw vs tfwx worldfiles!!!

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
            copy_raster_input = working_dir + filename_base + '.tif'
            sr = arcpy.Describe(copy_raster_input).spatialReference
            print(sr.factoryCode, sr.name)

            # if not web mercator auxiliary sphere then re-project
            print('reprojecting...')
            if sr.factoryCode != 3857:
                arcpy.ProjectRaster_management(
                    in_raster=copy_raster_input,
                    out_raster=working_dir + 'reprojected.tif',
                    out_coor_system="PROJCS['WGS_1984_Web_Mercator_Auxiliary_Sphere',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator_Auxiliary_Sphere'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],PARAMETER['Auxiliary_Sphere_Type',0.0],UNIT['Meter',1.0]]"
                )
                copy_raster_input = working_dir + 'reprojected.tif'
                print('reprojection success: ', copy_raster_input)

            print('running CopyRaster for conversion...')
            cog = working_dir + 'out_cog' + filename_base + '.tif'
            try:
                arcpy.CopyRaster_management(copy_raster_input, cog,
                                            nodata_value='256', format='COG', transform=True)
                print('uploading converted COG...')
                upload_key = 'bw/%s/%s_%s/index/cog/%s.tif' % (d[0], d[1], d[2], filename_base)
                client_s3.upload_file(cog, ls4_bucket, upload_key,
                                      ExtraArgs={
                                          'ACL': 'public-read',
                                          'ContentType': 'image/tiff'
                                      })
                print('cog upload success:', upload_key)

                print('invoking ls4-04-shp_index lambda...')
                payload = {'sourceBucket': ls4_bucket, 'sourceKey': upload_key}
                response = client_lambda.invoke(
                    FunctionName='ls4-04-shp_index',
                    InvocationType='Event',
                    Payload=json.dumps(payload)
                )
                print(response)

                print('using api to find collection_id...')
                url_string = "https://api.tnris.org/api/v1/historical/collections?scanned_index_ls4_links__icontains=s3.amazonaws.com/tnris-ls4/%s" % (d[4])
                print(url_string)
                api_res = requests.get(url_string).json()['results']
                if len(api_res) != 1:
                    print('%s collections contain the same scanned index ls4 link url' % str(len(api_res)))
                    print(api_res)
                    raise ValueError
                collection_id = api_res[0]['collection_id']

                print('updating LORE Index Service URL field for collection_id %s...' % collection_id)
                print('invoking api-tnris-org-update_database_record_utility lambda...')
                mapfile_url = "http://mapserver.tnris.org/wms/?map=/mapfiles/%s_%s_%s_index.map" % (
                                d[0].lower(), d[1].lower(), d[2])
                where = "id = '%s'" % collection_id
                payload = {
                    'table': 'historical_collection',
                    'field': 'index_service_url',
                    'value': mapfile_url,
                    'where': where
                }
                response = client_lambda.invoke(
                    FunctionName='api-tnris-org-update_database_record_utility',
                    InvocationType='Event',
                    Payload=json.dumps(payload)
                )
                print(response)

            except Exception as e:
                print(e)
                print(arcpy.GetMessages())

            print('INDEX SHEET FINAL SUCCESS:', q_bucket, tif, working_dir + filename_base + '.tif')
        counter += 1

else:
    print('bucket not declared. populate variables and try again.')

print("that's all folks!!")