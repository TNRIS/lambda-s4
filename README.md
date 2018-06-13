# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Overview

Project is an aerial image processing pipeline which utilizes a series of event driven lambda functions to watch the s3 bucket for .tif uploads with the necessary prefix. Upon upload, several lambda functions run in series to create overviews of the images and convert them to COG GeoTiffs and dump them into another prefixed section of the bucket. A footprint generation function is fired to create a shapefile footprint of all the associated images and upload it to an RDS PostGIS instance. Then a mapfile is created based on the new COGs and dumped into another prefixed section of the bucket where it is recognized by a Mapserver instance and hosts a WMS service of the imagery.

* Repo utilizes the s3 bucket 'tnris-ls4'
* Steps of the workflow/process outlined below step-by-step. Each step is stored within its own directory in this repo, numbered in order as `ls4-<step #>-gdal_<gdal command>`
* [RDC Steps](https://github.com/TNRIS/lambda-s4/wiki/RDC---Individual-Frames,-Indexes,-&-Lake-Gallery-Mosaics) found in this repo's
* Separate processing functions must be run for 1 band (grayscale) vs 3 band (natural color) rasters. The processing functions don't manipulate projection or NoData properties rasters. Therefore, upload prefixes (location) and appropriate formatting is required for the processing pipeline to run.
* Discovery of process and testing information outlined within `explroation_instructional.md` with all associated files within the './data' folder of this repo

---

## The Workflow

1. RDC uploads scanned image to  appropriate `.../scanned/...` directory in the tree for storage. No other event happen.
2. RDC uploads georeferenced image to appropriate `.../georef/...` directory in the tree. This fires the first lambda event.
3. `ls4-01-gdal_translate` runs generic DEFLATE compression on georeferenced tif and reuploads to same key but in a sub directory (environment variable defined). This fires the second lambda event.
4.

TODO: Bucket cleanup routine to delete anything that doesn't match t he rigid structure
* any non .tif or .ovr files
* folder structure
* file name structure
