# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Setup

* Install [qGIS](https://qgis.org/en/site/forusers/download.html): `sudo dnf update`, `sudo dnf install qgis qgis-python qgis-grass qgis-server`
* Install [GDAL](http://trac.osgeo.org/gdal/wiki/DownloadSource): download the .tar.gz, extract and `cd` into the folder, `./configure`, `sudo make`, `sudo make install`

## RDS Steps

1. scan frame as .tif and georeference, saving world file as per normal procedures
2. open ArcMap, add georeferenced .tif
3. export georefenced .tif as .tif with 'NoData' populated for handling the NoData field. This creates and saves a .tif with the proper header information and transparency for cells of no data. Note: this process does create another world file (.tfw) but this can be ignored - we won't be using it

## 'Test' Steps

1. Acquired '1960' georeferenced raster tifs from RDC
2. `gdalinfo athens_1960_export_test.tif` to print metadata about file
3. `gdalwarp -s_srs EPSG:4326 -t_srs EPSG:3857 athens_1960_export_test.tif reprojected173.tif` to reproject WGS84 tif -> WGS84 Web Mercator (4326 -> 3857)
4. `gdalinfo reprojected173.tif` to print metadata about output file ancd confirm reprojection

### Resources

* https://medium.com/planet-stories/a-handy-introduction-to-cloud-optimized-geotiffs-1f2c9e716ec3
