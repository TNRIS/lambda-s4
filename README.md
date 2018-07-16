# lambda-s4
Lambda S3 Services - Hosted raster tile services from AWS s3

## Overview

Project is an aerial image processing pipeline which utilizes a series of event driven lambda functions to watch the s3 bucket for .tif uploads with the necessary prefix. Upon upload, several lambda functions run in series to create overviews of the images and convert them to COG GeoTiffs and dump them into another prefixed section of the bucket. A footprint generation function is fired to create a shapefile footprint of all the associated images and upload it to an RDS PostGIS instance. Then a mapfile is created based on the new COGs and dumped into another prefixed section of the bucket where it is recognized by a Mapserver instance and hosts a WMS service of the imagery.

* Repo utilizes the s3 bucket 'tnris-ls4'
* Steps of the workflow/process outlined below step-by-step. Each step is stored within its own directory in this repo, numbered in order as `ls4-<step #>-<function task>`
* [RDC Steps](https://github.com/TNRIS/lambda-s4/wiki/RDC---Individual-Frames,-Indexes,-&-Lake-Gallery-Mosaics) found in this repo's
* Separate processing functions must be run for 1 band (grayscale) vs 3 band (natural color) rasters. The processing functions don't manipulate projection or NoData properties rasters. Therefore, upload prefixes (location) and appropriate formatting is required for the processing pipeline to run.
* Discovery of process and testing information outlined within `exploration_instructional.md` with all associated files within the './data' folder of this repo

Process output will be a WMS Service for each collection. The link will be: `http://mapserver.tnris.org/wms/?map=/mapfiles/<collection mapfile name>.map`

Collection Mapfile Naming Convention (all lowercase with natural spaces supplemented with underscores):
`<county name>_<agency name>_<yyyy>_<type>.map` or `<multi-county agency>_<mission code>_<type>.map` where type is 'frames', 'index', or 'mosaic'

Mapfile naming standard details outlined in the 'RDC Steps' link above.

---

## Setup

* Install [qGIS](https://qgis.org/en/site/forusers/download.html) for local testing (not used in functions themselves): `sudo dnf update`, `sudo dnf install qgis qgis-python qgis-grass qgis-server`
* Install [GDAL 2.3.0](http://trac.osgeo.org/gdal/wiki/DownloadSource): download the .tar.gz, extract and cd into the folder, ./configure, sudo make, sudo make install (fedora required a separate install of [jasper](http://download.osgeo.org/gdal/jasper-1.900.1.uuid.tar.gz) first) - or - ubuntu instruction [here](http://www.sarasafavi.com/installing-gdalogr-on-ubuntu.html)
* Install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and configure with proper key & secret
* Built with Python 3.6

---

## The Workflow

1. RDC uploads scanned image to  appropriate `.../scanned/...` directory in the tree for storage. No other event happens (this is just for availability to download at other times). Make public with 'public-read' ACL.
2. RDC uploads georeferenced image to appropriate `.../georef/...` directory in the tree. Make public with 'public-read' ACL. This triggers the first lambda function by an event wired to monitor the bucket for all tif extensions.
3. `ls4-01-compress` runs generic DEFLATE compression on georeferenced tif and reuploads to same key but in a sub directory (environment variable defined). Then it invokes the second lambda directly (doesn't use event because you cannot duplicate trigger on mulitple lambdas).
4. `ls4-02-overviews` creates overviews on the compressed tif and dumps them alongside it in the sub directory (.ovr). This function has a sub directory environment variable which it verifies is part of the compressed tif key in order to run -- **this means the sub directory environment variable for both functions must be the same**. This triggers the third lambda function by an event wired to monitor the bucket for all ovr extensions.
5. `ls4-03-cog` creates the cloud optimized geotiff (COG) from tif and ovr in the sub directory. Then it invokes the fourth lambda directly (doesn't use event because you cannot duplicate trigger on mulitple lambdas).
6. `ls4-04-shp_index` creates the shapefile tile index of all COGs in s3 for the collection. drops it off in s3. Then it uploads the tile index into the PostGIS RDS for use by mapfiles. This triggers the fifth lambda function by an event wired to monitor the bucket for all shp extensions.
7. `ls4-05-mapfile` creates the mapfile and uploads it to the s3 directory '/mapfiles' with the appropriate ec2 file ownership headers.

---

## MapServer

The Workflow of lambda functions maintain the imagery and mapfiles for all the services. The mapfiles are dumped into the s3 bucket in a subdirectory named 'mapfiles' (see note below about this folder's permissions). Independent of this workflow, is a dockerized Mapserver instance running within ECS in it's own cluser. It is within it's own cluster because it must be run on a custom AMI which has FUSE s3fs installed and the s3 bucket mounted as directory. This directory is shared as a volume to the running docker so the Mapserver looks in the bucket for mapfiles to serve under the illusion they are local. Instructions for creating the AMI are [here](http://adambreznicky.com/fuse_mapserver/) with included details related to permissions requirements. No special code is needed for the Mapserver instance (out-of-the-box configuration) so head over the TNRIS deployments repo for managing the instance with Terraform.

---

## Maintenance

`ls4-maintenance` is a Cloudwatch scheduled lambda function which runs every 24 hours and performs simple validation checks accross the project infrastructure. If invalid situations are identified, the function handles any deletions as necessary and then notifys a project SNS topic for developer awareness and potential follow up.

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
* zip contents and upload if testing. otherwise, head over to TNRIS deployments for the Terraform deployment of the functions and Mapserver instance.

---

## Output/Resulting Services

View the list of all services/mapfiles created and hosted by this project: `https://tnris.org/mapserver/`

---

## Notes
* s3 directory 'mapfiles' must be owned by the same user ('ec2-user') running on the ec2. this is accomplished by using fuse s3fs to mount the volume and using said user to `mkdir mapfiles` within the bucket. This only has to be done upon initial deployment of the whole project (a.k.a. shouldn't have to ever happen again); just noting in case tragedy requires entire infrastructure to be redone.
* 'MAP' & 'NAME' within mapfiles cannot be same as layer name or both draw in qgis/esri simultaneously
* Mapfiles require an AWS user key id and secret key to permit Mapserver access to the bucket. The user needs a policy with GET and PUT permissions to the bucket. These are utilized by `ls4-05-mapfile` function and pulled as environment variables
* [Project Narrative](http://adambreznicky.com/cog_machine/) with overview of lambda functions and instructions for setting up Mapserver
