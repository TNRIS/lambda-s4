this sandbox used for miscellaneous scripts related to QC and bulk geotiff processing within s3 Q drive conversion into ls4 engine/ls4 s3 bucket.

current project status:
* clean ls4 s3 bucket only contained scanned indexes with no georef/ or cog/ files.
* Q drive s3 backup clean insofar as containing all ls4 scanned indexes (previous bullet) with associated georeference files (.ovr, and world files-- either .tfw or .tfwx with .aux.xml)
* bulk 'process_georef_index.py' ran in aws workspace to utilize arcpy, processing bullet 2 Q drive files based on bullet 1 ls4 files list, and dumping results into ls4 engine (ls4 s3 bucket collection's georef/ folder)
* Q drive s3 backup also has all other remnents and yet-to-be-processed scanned indexes (and county mosaics and frames, of course)

yet-to-be-processed in ls4 bucket (current exceptions written into processing script):
1. anything NOT `/index/scanned`
2. USAF agency

yet-to-be-processed in Q bucket (current exceptions written into qc scripts):
1. `2k19_summer_reorg_Special_Scanes` folder
2. `MultiCounty` folder
3. AMS agency
4. USAF agency
5. _LI_ line indexes
6. _CM county mosaics
7. ACOE agency
8. USGS agency? -- ElPaso, USGA, 1936 sheets 1-6 coooouullld be processed. any other for this agency exist?
9. AMMANN agency? agency representation is non-regular right now. title case, all caps, and alternative spellings all exist
10. Fairchild agency??


TO DO:
1. write verification count QC script to verify all was processed successfully
2. update processing script to identify # of collections being processed, not just # of sheets
3. write QC script to identify all variations of AMMANN agency. list for RDC to fix. title case, all caps, and alternative spellings all exist
4. write QC script to identify lists of all yet-to-be-procesed exceptions. each individual list will be separate cleanup and processing workflow.


To re-run script, need to:
1. delete mapfiles from ls4 s3
2. delete dbase tables within ls4 rds
3. run script, delete all non-index/scanned/ ls4 bucket files (georef tifs, index shapefiles, index zipfiles, cog/ folder)