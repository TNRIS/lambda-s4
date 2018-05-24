# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Setup

* Install [qGIS](https://qgis.org/en/site/forusers/download.html): `sudo dnf update`, `sudo dnf install qgis qgis-python qgis-grass qgis-server`
* Install [GDAL](http://trac.osgeo.org/gdal/wiki/DownloadSource): download the .tar.gz, extract and cd into the folder, ./configure, sudo make, sudo make install - or - ubuntu instruction [here](http://www.sarasafavi.com/installing-gdalogr-on-ubuntu.html)
* Install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and configure with proper key & secret

## Overview

* Repo utilizes the s3 bucket 'tnris-ls4'

## RDS Steps

1. scan frame as .tif and georeference, saving world file as per normal procedures
2. open ArcMap, add georeferenced .tif
3. export georefenced .tif as .tif with 'NoData' populated for handling the NoData field. This creates and saves a .tif with the proper header information and transparency for cells of no data. Note: this process does create another world file (.tfw) but this can be ignored - we won't be using it

## 'Test' Steps

##### initial data formatting
1. Acquired '1960' georeferenced raster tifs from RDC
2. `gdalinfo athens_1960_export_test.tif` to print metadata about file
3. `gdalwarp -s_srs EPSG:4326 -t_srs EPSG:3857 athens_1960_export_test.tif reprojected173.tif` to reproject WGS84 tif -> WGS84 Web Mercator (4326 -> 3857)
4. `gdalinfo reprojected173.tif` to print metadata about output file ancd confirm reprojection

##### test data s3 setup
5. `make put-test-data` from the repo root directory to upload the complete sample group of frames from s3 (GeoTiff folder)
6. `make get-test-data` from the repo root directory to download the complete sample group of frames from s3 (GeoTiff folder)

##### quick mosaic test
7. `gdalbuildvrt ./mosaic.virt ./01-30-60_5-15.tif ./01-30-60_5-30.tif ./02-08-60_6-107.tif ./02-08-60_6-109.tif ./02-0860_6-111.tif ./01-29-60_4-173.tif ./01-29-60_4-175.tif` to create a virt for outlining a merge amongst the sample tifs
8. `gdal_translate -of GTiff ./mosaic.virt ./mosaic.tif` to perform the mosaic/merge on the sample tifs

##### generate COGs
9. `cd ./data/test/1960/ && mkdir COG`
10. `cd ../GeoTiff`
11. `gdal_translate ./01-29-60_4-173.tif ../COG/01-29-60_4-173.tif -co TILED=YES -co COPY_SRC_OVERVIEWS=YES -co COMPRESS=LZW`

### Resources

* https://medium.com/planet-stories/a-handy-introduction-to-cloud-optimized-geotiffs-1f2c9e716ec3
* https://medium.com/planet-stories/cloud-native-geospatial-part-2-the-cloud-optimized-geotiff-6b3f15c696ed
* https://trac.osgeo.org/gdal/wiki/CloudOptimizedGeoTIFF
* http://www.cogeo.org/
