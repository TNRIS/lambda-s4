#!/bin/bash

filenames=""
for file in ./GeoTiff/*.tif
do
  echo $file
  name="${file##*/}"
  gdal_translate $file ./COG/$name -co TILED=YES -co COPY_SRC_OVERVIEWS=YES -co COMPRESS=LZW
  python validate_cloud_optimized_geotiff.py ./COG/$name
  if [ $name != "mosaic.tif" ]
  then
    spaced="./GeoTiff/$name "
    filenames+=$spaced
  fi
done

echo "indexing raster footprint"
echo $filenames
gdaltindex ./COG/mosaic_footprint.shp $filenames
echo "raster footprint created"

echo "tifs converted to cog successfully."
