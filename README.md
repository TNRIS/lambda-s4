# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Overview

Project is an aerial image processing pipeline which utilizes a series of event driven lambda functions to watch the s3 bucket for .tif uploads with the necessary prefix. Upon upload, several lambda functions run in series to create overviews of the images and convert them to COG GeoTiffs and dump them into another prefixed section of the bucket. A footprint generation function is fired to create a shapefile footprint of all the associated images and upload it to an RDS PostGIS instance. Then a mapfile is created based on the new COGs and dumped into another prefixed section of the bucket where it is recognized by a Mapserver instance and hosts a WMS service of the imagery.

* Repo utilizes the s3 bucket 'tnris-ls4'
* [RDC Steps](https://github.com/TNRIS/lambda-s4/wiki/RDC---Individual-Frames,-Indexes,-&-Lake-Gallery-Mosaics) found in this repo's
* Separate processing functions must be run for 1 band (grayscale) vs 3 band (RGB) rasters. The processing functions don't manipulate projection or NoData properties rasters. Therefore, upload prefixes (location) and appropriate formatting is required for the processing pipeline to run.

---


TODO: Bucket cleanup routine to delete anything that doesn't match t he rigid structure
