
put-test-data:
	aws s3 cp ./data/test/1960/GeoTiff/ s3://tnris-ls4/test/1960/GeoTiff/ --recursive

get-test-data:
	aws s3 cp s3://tnris-ls4/test/1960/GeoTiff/ ./data/test/1960/GeoTiff/ --recursive
