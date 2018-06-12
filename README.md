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
