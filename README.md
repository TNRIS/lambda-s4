# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Overview

Project is an aerial image processing pipeline which utilizes a series of event driven lambda functions to watch the s3 bucket for .tif uploads with the necessary prefix. Upon upload, several lambda functions run in series to create overviews of the images and convert them to COG GeoTiffs and dump them into another prefixed section of the bucket. A footprint generation function is fired to create a shapefile footprint of all the associated images and upload it to an RDS PostGIS instance. Then a mapfile is created based on the new COGs and dumped into another prefixed section of the bucket where it is recognized by a Mapserver instance and hosts a WMS service of the imagery.

* Repo utilizes the s3 bucket 'tnris-ls4'
* Steps of the workflow/process outlined below step-by-step. Each step is stored within its own directory in this repo, numbered in order as `ls4-<step #>-<function task>`
* [RDC Steps](https://github.com/TNRIS/lambda-s4/wiki/RDC---Individual-Frames,-Indexes,-&-Lake-Gallery-Mosaics) found in this repo's
* Separate processing functions must be run for 1 band (grayscale) vs 3 band (natural color) rasters. The processing functions don't manipulate projection or NoData properties rasters. Therefore, upload prefixes (location) and appropriate formatting is required for the processing pipeline to run.
* Discovery of process and testing information outlined within `exploration_instructional.md` with all associated files within the './data' folder of this repo

---

## The Workflow

1. RDC uploads scanned image to  appropriate `.../scanned/...` directory in the tree for storage. No other event happens (this is just for availability to download at other times).
2. RDC uploads georeferenced image to appropriate `.../georef/...` directory in the tree. This triggers the first lambda function by an event wired to monitor the bucket for all tif extensions.
3. `ls4-01-compress` runs generic DEFLATE compression on georeferenced tif and reuploads to same key but in a sub directory (environment variable defined). Then it invokes the second lambda directly (doesn't use event because you cannot duplicate trigger on mulitple lambdas).
4. `ls4-02-overviews` creates overviews on the compressed tif and dumps them alongside it in the sub directory (.ovr). This function has a sub directory environment variable which it verifies is part of the compressed tif key in order to run -- **this means the sub directory environment variable for both functions must be the same**. This triggers the third lambda function by an event wired to monitor the bucket for all ovr extensions.
5. `ls4-03-cog` creates the cloud optimized geotiff (COG) from tif and ovr in the sub directory. Then it invokes the fourth lambda directly (doesn't use event because you cannot duplicate trigger on mulitple lambdas).
6. `ls4-04-shp_index` creates the shapefile tile index of all COGs in s3 for the collection. drops it off in s3.

---

## Rasterio needs ManyLinux Wheels

* `cd ls4-04-shp_index` and `pip install -r requirements.txt`. [info here](https://github.com/mapbox/rasterio/issues/942) on installing with `pip install --pre rasterio[s3]>=1.0a4`. Problem is the deployment package is too large. It must be < 50mb to upload directly to lambda. If larger, we can upload to s3 and point lambda to it but unzipped still must be < 250mb (which this isn't...). [idea here](https://medium.com/@mojodna/slimming-down-lambda-deployment-zips-b3f6083a1dff) and [here](https://github.com/lambci/docker-lambda) and [here](https://github.com/perrygeo/lambda-rasterio). getting atime to work [required this](https://bugzilla.redhat.com/show_bug.cgi?id=756670)

## Deployment

* `ls4-04-shp_index` python requires packing dependencies into zipfile for deployment. Do this by running `make pack-ls4-04-shp_index` from the repo folder

TODO: Bucket cleanup routine to delete anything that doesn't match t he rigid structure
* any non .tif or .ovr files
* folder structure
* file name structure
