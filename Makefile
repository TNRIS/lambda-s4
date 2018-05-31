
put-test-data:
	aws s3 cp ./data/test/1960/GeoTiff/ s3://tnris-ls4/test/1960/GeoTiff/ --acl public-read --recursive

get-test-data:
	aws s3 cp s3://tnris-ls4/test/1960/GeoTiff/ ./data/test/1960/GeoTiff/ --recursive

put-test-cogs:
	aws s3 cp ./data/test/1960/COG/ s3://tnris-ls4/test/1960/COG/ --acl public-read --recursive

get-test-cogs:
	aws s3 cp s3://tnris-ls4/test/1960/COG/ ./data/test/1960/COG/ --recursive
