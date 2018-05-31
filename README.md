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

* Overview

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
15.

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
