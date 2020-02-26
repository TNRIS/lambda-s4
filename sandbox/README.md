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
1. write verification count QC script to verify all was processed successfully & database updated with mapfile url. 
2. update processing script to identify # of collections being processed, not just # of sheets
3. write QC script to identify all variations of AMMANN agency. list for RDC to fix. title case, all caps, and alternative spellings all exist
4. write QC script to identify lists of all yet-to-be-procesed exceptions. each individual list will be separate cleanup and processing workflow.

Error fix in post:
1. Garza USDA 1951 Sheets 1-3 (4 was successful) - Counter # 2048-2050
2. Bell TxDOT 1985 Sheet 1


To re-run script, need to:
1. delete mapfiles from ls4 s3
2. delete dbase tables within ls4 rds
3. run script, delete all non-index/scanned/ ls4 bucket files (georef tifs, index shapefiles, index zipfiles, cog/ folder)


## ESRI Python Packages in Lambda:
emailed esri about getting Arcpy to work in lambda,they responded with this [link](https://www.georgebochenek.com/posts/arcgis-in-lambda/). The instructions are a bit out dated but the general workflow worked. Notes to take into account:

1. a few attempts were made to make this work. rather than try to repackage it all up, zipfile copies have been saved in s3 (tnris-misc/esriPythonPackages) and should just be retrieved from there. 
   * `arcgisLambda.zip` is the result of directly following the blog instructions. only contains the 'arcgis' package (limited, focused on AGO, non-standard tools) and was built using python 3.7. Doesn't contain the right tools for any purposes related to this project which is why alternative attempts were made.
   * `arcpyLambda.zip` is the result of referencing [this tech support article](https://support.esri.com/en/technical-article/000012501) alongside [this installation information](https://enterprise.arcgis.com/en/server/latest/administer/linux/linux-python.htm). This second attempt contains the 'arcgis', 'arcgisscripting', and 'arcpy' packages from the arcgis-server-py3 conda install and was built using python 3.6. In order to accomplish this, anaconda was [reinstalled using v5.2 to get python 3.6](https://stackoverflow.com/questions/54801513/how-can-i-download-anaconda-for-python-3-6), also [reference](http://chris35wills.github.io/conda_python_version/#:~:text=To%20change%20your%20python%20version,maybe%20conda%20install%20python%3D2.7.).
2. the free tier machine would hit errors when working with conda installs... seemed to be not enough RAM. had to spin up a larger machine to accomplish all this.
3. In step 5 of the blog instructions, `python3` install doesn't work, requires using the specific minor version also: i.e. `sudo yum install python36`
4. temporarily configured the aws-cli with credentials to simply upload to s3 rather than scp the output zipfile back onto the local machine