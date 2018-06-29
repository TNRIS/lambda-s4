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

1. RDC uploads scanned image to  appropriate `.../scanned/...` directory in the tree for storage. No other event happens (this is just for availability to download at other times). Make public with 'public-read' ACL.
2. RDC uploads georeferenced image to appropriate `.../georef/...` directory in the tree. Make public with 'public-read' ACL. This triggers the first lambda function by an event wired to monitor the bucket for all tif extensions.
3. `ls4-01-compress` runs generic DEFLATE compression on georeferenced tif and reuploads to same key but in a sub directory (environment variable defined). Then it invokes the second lambda directly (doesn't use event because you cannot duplicate trigger on mulitple lambdas).
4. `ls4-02-overviews` creates overviews on the compressed tif and dumps them alongside it in the sub directory (.ovr). This function has a sub directory environment variable which it verifies is part of the compressed tif key in order to run -- **this means the sub directory environment variable for both functions must be the same**. This triggers the third lambda function by an event wired to monitor the bucket for all ovr extensions.
5. `ls4-03-cog` creates the cloud optimized geotiff (COG) from tif and ovr in the sub directory. Then it invokes the fourth lambda directly (doesn't use event because you cannot duplicate trigger on mulitple lambdas).
6. `ls4-04-shp_index` creates the shapefile tile index of all COGs in s3 for the collection. drops it off in s3. Then it uploads the tile index into the PostGIS RDS for use by mapfiles. This triggers the fifth lambda function by an event wired to monitor the bucket for all shp extensions.
7. `ls4-05-mapfile` create the mapfile and uploads it to the s3 directory '/mapfiles' with the appropriate ec2 file ownership headers. s3 directory 'mapfiles' must be owned by the same user. this is accomplished by using fuse s3fs to mount the volume and using said user to `mkdir mapfiles` within the bucket. Mapfile 'MAP' 'NAME' cannot be same as layer name or both draw
8.

TODO:
-setup fuse with ecs ami
-mapfile upload with proper headers
-setup windows fuse for scanned/ & georef/ uploads. configure to be done as public-read ACL

---

## Rasterio needs ManyLinux Wheels

* `cd ls4-04-shp_index` and `pip install -r requirements.txt`. [info here](https://github.com/mapbox/rasterio/issues/942) on installing with `pip install --pre rasterio[s3]>=1.0a4`
* Problem is the deployment package is too large. It must be < 50mb to upload directly to lambda. If larger, we can upload to s3 and point lambda to it but unzipped still must be < 250mb (which this isn't...).
* This means we must use `atime` (accessed/modified time) metadata on the filesystem after running the function locally to identify the wheat from the chaff in all the dependency packages. [Problem and atime usage method described here](https://medium.com/@mojodna/slimming-down-lambda-deployment-zips-b3f6083a1dff). [On Fedora, i had to enable atime using 'strictatime'](https://bugzilla.redhat.com/show_bug.cgi?id=756670).
* General 'atime' process to removed unused dependency files:
  1. enable atime file metadata
  2. cd into function. dependencies requirements need to be installed and moved into this directory as if ready for lambda deployment (`make pack-%` from root to move dependencies)
  3. create arbitrary file to compare against (`touch start`)
  4. run function
  5. create txt list of files with atime later than arbitrary file. these are the files in the dependencies that are actually used by the function: `find <path to function> -type f -anewer ./start > dep_whitelist.txt`
  6. run dep_cleanup.py (depends on 'dep_whitelist.txt' file) to remove all unused files from function folder
  7. zip function and deploy
* Originally: 7,716 items - 344.0 MB
* After dep_cleanup: 2,072 items - 154.0 MB (44 MB compressed!)

---

## Deployment

* `ls4-04-shp_index` & `ls4-05-mapfile` are python functions which require copying dependencies from site-packages to function folder for deployment.
* JS functions only have their `./bin/<gdal binary>` as a dependency and don't need others transferred.
* if using separate virtual envs for python functions (**as you should be**) then enable it for the function being deployed.
* `ls4-04-shp_index` is a special case as it uses Rasterio and ManyLinux Wheels. See section above on preparing its' dependencies for deployment as it differs from any other lambda preparation.
* then run `make pack-<function/folder name>` from project root to copy dependencies from site-packages into function folder.
* zip contents for upload.

TODO: Bucket cleanup routine to delete anything that doesn't match t he rigid structure
* any non .tif or .ovr files
* folder structure
* file name structure
