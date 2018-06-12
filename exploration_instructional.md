# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Setup

* Install [qGIS](https://qgis.org/en/site/forusers/download.html): `sudo dnf update`, `sudo dnf install qgis qgis-python qgis-grass qgis-server`
* Install [GDAL 2.3.0](http://trac.osgeo.org/gdal/wiki/DownloadSource): download the .tar.gz, extract and cd into the folder, ./configure, sudo make, sudo make install (fedora required a separate install of [jasper](http://download.osgeo.org/gdal/jasper-1.900.1.uuid.tar.gz) first) - or - ubuntu instruction [here](http://www.sarasafavi.com/installing-gdalogr-on-ubuntu.html)
* Install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and configure with proper key & secret

## Overview

* Repo utilizes the s3 bucket 'tnris-ls4'

---

## RDS Steps

1. scan frame as .tif and georeference, saving world file as per normal procedures
2. open ArcMap, add georeferenced .tif
3. export georefenced .tif as .tif with '256' populated for handling the NoData field. This creates and saves a .tif with the proper header information and transparency for cells of no data. Note: this process does create another world file (.tfw) but this can be ignored - we won't be using it

---

## Mapserver/GDAL/s3/Lambda

* Serving Batch of COGs Overview (Step #20+)

1. list COGs keynames and prepend /vsis3/ and save to a list
2. use that file list with gdaltindex (gdal v2.3) to shapefile raster tile index
3. 'Location' column should have `/vsis3/<keyname>.tif`
4. load the shapefile raster index into PostgreSQL
5. create Mapserver Map file
6. Use COGs with dockerized Mapserver/GDAL

* Detail

1. Created RDS and s3 bucket
2. Created IAM roles for lambda and ec2. Gave both AWSLambdaFullAccess policies
3. Created EC2 instance and dumped sample tifs into s3 bucket
4. SSH'd onto ec2 and tested access by pulling down sample tifs from s3 bucket
5. **Test-** List contents in bucket with folder key: `aws s3 ls --request-payer requester s3://tnris-ls4/test/1960/GeoTiff/`
6. **Test-** Narrow down list to .tif: `aws s3 ls --request-payer requester s3://tnris-ls4/test/1960/GeoTiff/ | grep ".*\.tif$"`
7. Write keynames to list: `sudo aws s3 ls --request-payer requester --recursive s3://tnris-ls4/test/1960/GeoTiff/ | grep ".*\.tif$" | awk -F" " '{print $4}' > mylist`
8. **Test-** Verify list was written with: `cat mylist`
9. One at a time, copied each of the 3 `aws lambda create-function....` commands from './data/test/create_lambda.txt' and ran them from the ec2 to create the 3 lambda COG generation functions. They create the function with code pulled from Korver's s3 bucket and set approprate environment variables. **AWS lambda iam ARN removed for git security. need to replace for replication**
10. In aws console, created a test for the 'lambda-gdal_translate-cli' function with this input json:
``` json
{
"sourceBucket": "aws-naip",
"sourceKey": "ct/2014/1m/rgbir/41072/m_4107243_nw_18_1_20140721.tif"
}
```
11. Ran test which created new key in bucket: `cloud-optimize/deflate/ct/2014/100cm/rgb/41072/m_4107243_nw_18_1_20140721.tif`
12. In aws console, opened the 'lambda-gdaladdo-evt' function and configured an s3 event:
  * Bucket: `tnris-ls4`
  * Event Type: `Object Created`
  * Prefix: `cloud-optimize/deflate/`
  * Filter: `tif`
13. In aws console, opened the 'lambda-gdal_translate-evt' function and configured an s3 event:
  * Bucket: `tnris-ls4`
  * Event Type: `Object Created`
  * Prefix: `cloud-optimize/deflate/`
  * Filter: `ovr`
14. Re-ran test created in step #10. This output the original tif (same as step #11), an .ovr for said tif, and an optimized .tif
15. Copied .tif files within bucket from /test/1960/GeoTiff/ to /cloud-optimize/defalte/ct/2014/rgb/41072/ so that i could test the lambda sequence on these tifs
16. Ran `sudo aws s3 ls --request-payer requester --recursive s3://tnris-ls4/cloud-optimize/deflate/ct/2014/100cm/rgb/41072/ | grep ".*\.tif$" | awk -F" " '{print $4}' > mylist` to regenerate list
17. Removed `-b 2 -b 3` band arguments, and set 'uploadKeyPrefix' to an empty string on the lambda-gdal_translate-cli lambda environment variables since we are sample testing 1 band rasters (not 3 as with the other naip test tif)
18. Changed "gdalArgs" environment variable to `-of GTiff -ot Byte -a_nodata 256 -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 -co COMPRESS=DEFLATE -co COPY_SRC_OVERVIEWS=YES --config GDAL_TIFF_OVR_BLOCKSIZE 512` for lambda-gdal_translate-evnt lambda function to account for the single band
19. Ran the sequence of lambda functions on 'mylist' of tifs: `cat mylist | grep ".*\.tif$" | awk -F"/" '{print "lambda invoke --function-name lambda-gdal_translate-cli --region us-east-1 --invocation-type Event --payload \x27{\"sourceBucket\":\"tnris-ls4\",\"sourceKey\":\""$0"\"}\x27 log" }' | xargs -n11 -P64 aws`
20. On local machine( it has gdal installed)::: Create list of output (COG) keys with vsis3 prefix `aws s3 ls --recursive s3://tnris-ls4/cloud-optimize/final/ct/2014/100cm/rgb/41072/ | grep ".*\.tif$" | awk -F" " '{print "/vsis3/tnris-ls4/" $4}' > mykeys.txt`
21. `tac mykeys.txt > mykeys_r.txt` to reverse the order of the frames so index polys are sorted properly. This was done for testing but is not really necessary and can be skipped in the future.
21. `mkdir indexSRS` and then Create index shapefile using COG list from previous step `gdaltindex -src_srs_name src_srs ./indexSRS/index.shp --optfile ./mykeys_r.txt`
22. Put the index into s3 `aws s3 cp ./indexSRS/ s3://tnris-ls4/cloud-optimize/final/index/ --acl public-read --recursive`
23. Installed 'shp2pgsql' locally
24. Uploaded index to postgres `shp2pgsql -s 4326 -d -g the_geom ./indexSRS/index.shp test_index |psql -U <username> -p 5432 -h <host> <dbname>`
25. On ec2 again... `aws s3 sync s3://tnris-ls4/cloud-optimize/final/index /home/ec2-user/mapfiles` to copy the shapefiles from the s3 Bucket
26. Created 'test.map' mapfile within /mapfiles directory on ec2. sample mapfile located in /data/test/test.map of this repo.
27. `yum install -y docker`
28. `sudo service docker start`
29. `sudo docker run --detach -v /home/ec2-user/mapfiles:/mapfiles:ro --publish 8080:80 --name mapserver geodata/mapserver`
30. `sudo docker exec mapserver touch /var/log/ms_error.log`
31. `sudo docker exec mapserver chown www-data /var/log/ms_error.log`
32. `sudo docker exec mapserver chmod 644 /var/log/ms_error.log`. then use `sudo docker exec mapserver cat /var/log/ms_error.log` to view logs.

Working issues:

33. Instructional url (didnt use it)  http://ec2-34-201-112-166.compute-1.amazonaws.com:8080/wms/?map=/mapfiles/test.map&SERVICE=WMS&LAYERS=test_frames&SRS=epsg:4326&BBOX=-95.7362749,32.2025543,-95.6835030,32.1582697&STYLES=&VERSION=1.1.1&REQUEST=GetMap&WIDTH=256&HEIGHT=256%EF%BB%BF
34. WMS URL (used in qgis) `http://ec2-34-201-112-166.compute-1.amazonaws.com:8080/wms/?map=/mapfiles/test.map` in qgis to connect to sever. *Needed to designate WGS84 as projection and tile size as 512x512*
35. Went into s3 bucket to make COGs public read.
36. `http://ec2-34-201-112-166.compute-1.amazonaws.com:8080/wms/?map=/mapfiles/test.map&SERVICE=WMS&VERSION=1.1.1 &REQUEST=GetCapabilities` to get the GetCapabilites.xml
37. had installed pip and aws cli in docker but was in vain i believe... skipping here...
38. Manually created `lambda-s4-mapserver` user with manually created policy `tnris-ls4-mapserver-access` for use within the mapfiles by the MapServer docker to access tnris-ls4 bucket.
39. **higher compression? s3 files make public. change coordinate system-- all must be 3857 at start. add filename as attribute to index shp. s3 as drive on ubuntu for mapfiles (lambda will create mapfiles and drop in s3, while host ami will have s3 bucket mapped as local drive to access them and provide them to the mapserver docker). setup wmts.**
40. Added TWDB IP to jenkins security group for testing WMS on esri windows computer

Mount s3:

41. [used these basic instructions](https://cloudkul.com/blog/mounting-s3-bucket-linux-ec2-instance/) to install fuse and mount s3 as a drive on the server.
42. setup permissions using lambda-s4-mapserver iam key and secret. be sure to chown the .passwd-s3fs file in the user's $HOME directory to the ec2-user user. [specific permissions](https://github.com/s3fs-fuse/s3fs-fuse/wiki/Fuse-Over-Amazon) necessary for passwd-s3fs file
43. sudo edit /etc/fuse.conf to uncomment out the `user_allow_other` line. this permits mounting the s3 bucket and allowing other users to access it.
44. `s3fs tnris-ls4 -o multireq_max=5 -o allow_other ./tnris-ls4` to mount. `sudo umount ./tnris-ls4` to unmount.
45. `sudo docker run --detach -v /home/ec2-user/tnris-ls4/testt:/mapfiles:ro --publish 8080:80 --name mapserver geodata/mapserver` to run mapserver with s3 as the mapfiles directory. then run steps 30-32 for logging.
46. `sudo chown ec2-user ./tnris-ls4/testt/test2.map` change owner of new mapfile. then `chmod 664 ./tnris-ls4/testt/test2.map` to change permission (https://github.com/s3fs-fuse/s3fs-fuse/issues/333)
**database credentials are in the mapfile! needs to be handled?**
47. set encryption key as environment variable on ec2 instance (and eventually ami), pass it to the docker on run with `-e` flag, then have the mapfiles use it to unencrypt the secrets with a `CONFIG "MS_ENCRYPTION_KEY" ""`. see step #49, followed up on but can be ignored.
48. To resolve #46 - python programmatically uploaded mapfiles need to be uploaded to s3 with custom http headers identifying 'ec2-user's uid, gid, and the required mtime & mode.
``` python
import boto3
s3 = boto3.resource('s3')
s3.Bucket('tnris-ls4').upload_file('/<path to file>/test.map','testt/test2.map',ExtraArgs={'Metadata':{'mode':'33204','uid':'500','gid':'500','mtime':'1528814551'}})
```
49. [created encryption key on mapserver docker](http://mapserver.github.io/nl_NL/utilities/msencrypt.html) but this probably won't be necessary as all mapfiles will be on lockdown in s3. ignore this step.

Creating new mapfiles programmatically:
`sed -i 's/oldstring/newstring/g' filename` to replace string pieces in file


---

## Experiment

##### initial data formatting
1. Acquired '1960' georeferenced raster tifs from RDC
2. `gdalinfo athens_1960_export_test.tif` to print metadata about file
3. `gdalwarp -s_srs EPSG:4326 -t_srs EPSG:3857 athens_1960_export_test.tif reprojected173.tif` to reproject WGS84 tif -> WGS84 Web Mercator (4326 -> 3857)
4. `gdalinfo reprojected173.tif` to print metadata about output file ancd confirm reprojection

##### test data s3 setup
5. `make put-test-data` from the repo root directory to upload the complete sample group of frames from s3 (GeoTiff folder)
6. `make get-test-data` from the repo root directory to download the complete sample group of frames from s3 (GeoTiff folder)

##### quick mosaic test
7. `gdalbuildvrt -srcnodata 256 ./mosaic.virt ./01-29-60_4-175.tif ./01-29-60_4-173.tif ./02-0860_6-111.tif ./02-08-60_6-109.tif ./02-08-60_6-107.tif ./01-30-60_5-30.tif ./01-30-60_5-15.tif` to create a virt for outlining a merge amongst the sample tifs
8. `gdal_translate -of GTiff ./mosaic.virt ./mosaic.tif` to perform the mosaic/merge on the sample tifs
9. `gdaladdo -ro ./mosaic.tif` to create mosaic overlays (requires gdal v2.3.0!)

##### generate COGs and footprint
10. `cd ./data/test/1960/ && mkdir COG`
11. `. ./cog_converter.sh` will run a bash script to batch convert all .tif files in 'GeoTiff' folder to cogs in 'COG' folder. will also generate a bounding box footprint for all rasters processed *(except mosaic.tif footprint, but this can easily be implemented by removing the 'if' statement in the shell script)*
12. **OPTIONAL:** `python validate_cloud_optimized_geotiff.py ./COG/01-29-60_4-173.tif` verifies the output is cloud optimized. Had to install gdal python package with Anaconda (`conda install gdal`) to run it. Implemented into 'cog_converter.sh' script so doesn't need to be run individually

##### Alternative Approach
1. `. ./alternator.sh`

##### Resources

* https://medium.com/planet-stories/a-handy-introduction-to-cloud-optimized-geotiffs-1f2c9e716ec3
* https://medium.com/planet-stories/cloud-native-geospatial-part-2-the-cloud-optimized-geotiff-6b3f15c696ed
* https://trac.osgeo.org/gdal/wiki/CloudOptimizedGeoTIFF
* http://www.cogeo.org/
* Alternative: https://astuntech.atlassian.net/wiki/spaces/ISHAREHELP/pages/14844053/Mosaic+thousands+of+raster+images
