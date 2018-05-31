# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Setup

* Install [qGIS](https://qgis.org/en/site/forusers/download.html): `sudo dnf update`, `sudo dnf install qgis qgis-python qgis-grass qgis-server`
* Install [GDAL 2.3.0](http://trac.osgeo.org/gdal/wiki/DownloadSource): download the .tar.gz, extract and cd into the folder, ./configure, sudo make, sudo make install (fedora required a separate install of [jasper](http://download.osgeo.org/gdal/jasper-1.900.1.uuid.tar.gz) first) - or - ubuntu instruction [here](http://www.sarasafavi.com/installing-gdalogr-on-ubuntu.html)
* Install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and configure with proper key & secret

## Overview

* Repo utilizes the s3 bucket 'tnris-ls4'

## RDS Steps

1. scan frame as .tif and georeference, saving world file as per normal procedures
2. open ArcMap, add georeferenced .tif
3. export georefenced .tif as .tif with '256' populated for handling the NoData field. This creates and saves a .tif with the proper header information and transparency for cells of no data. Note: this process does create another world file (.tfw) but this can be ignored - we won't be using it

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
7. `gdalbuildvrt -srcnodata 256 ./mosaic.virt ./01-29-60_4-175.tif ./01-29-60_4-173.tif ./02-0860_6-111.tif ./02-08-60_6-109.tif ./02-08-60_6-107.tif ./01-30-60_5-30.tif ./01-30-60_5-15.tif` to create a virt for outlining a merge amongst the sample tifs
8. `gdal_translate -of GTiff ./mosaic.virt ./mosaic.tif` to perform the mosaic/merge on the sample tifs
9. `gdaladdo -ro ./mosaic.tif` to create mosaic overlays (requires gdal v2.3.0!)

##### generate COGs and footprint
10. `cd ./data/test/1960/ && mkdir COG`
11. `. ./cog_converter.sh` will run a bash script to batch convert all .tif files in 'GeoTiff' folder to cogs in 'COG' folder. will also generate a bounding box footprint for all rasters processed *(except mosaic.tif footprint, but this can easily be implemented by removing the 'if' statement in the shell script)*
12. **OPTIONAL:** `python validate_cloud_optimized_geotiff.py ./COG/01-29-60_4-173.tif` verifies the output is cloud optimized. Had to install gdal python package with Anaconda (`conda install gdal`) to run it. Implemented into 'cog_converter.sh' script so doesn't need to be run individually

---

### Alternative Approach
1. `. ./alternator.sh`

---

### Mapserver/GDAL/S3/Lambda


---

### Resources

* https://medium.com/planet-stories/a-handy-introduction-to-cloud-optimized-geotiffs-1f2c9e716ec3
* https://medium.com/planet-stories/cloud-native-geospatial-part-2-the-cloud-optimized-geotiff-6b3f15c696ed
* https://trac.osgeo.org/gdal/wiki/CloudOptimizedGeoTIFF
* http://www.cogeo.org/

Alterative:

* https://astuntech.atlassian.net/wiki/spaces/ISHAREHELP/pages/14844053/Mosaic+thousands+of+raster+images
