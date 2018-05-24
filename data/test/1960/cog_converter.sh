#!/bin/bash

for file in ./GeoTiff/*.tif
do
  echo $file
  name="${file##*/}"
  gdal_translate $file ./COG/$name -co TILED=YES -co COPY_SRC_OVERVIEWS=YES -co COMPRESS=LZW
done

echo "tifs converted to cog successfully."
