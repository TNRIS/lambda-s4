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

echo "tifs converted to cogs."

# echo "indexing raster footprint"
# echo $filenames
# gdaltindex ./COG/mosaic_footprint.shp $filenames
# echo "raster footprint created"

gdalbuildvrt ./COG/all_tif.vrt ./COG/*.tif -a_srs "EPSG:3857"
echo "vrt built."

gdaladdo -ro --config COMPRESS_OVERVIEW JPEG --config INTERLEAVE_OVERVIEW PIXEL --config BIGTIFF_OVERVIEW YES ./COG/all_tif.vrt
echo "overviews created."
