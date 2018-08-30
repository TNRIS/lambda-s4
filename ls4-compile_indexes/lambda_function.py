# --------------- IMPORTS ---------------
import os
import boto3
import psycopg2
from geojson import FeatureCollection, dump
import json

# Database Connection Info
database = os.environ.get('DB_NAME')
username = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
host = os.environ.get('DB_HOST')
port = os.environ.get('DB_PORT')
upload_bucket = os.environ.get('uploadBucket')

conn_string = "dbname='%s' user='%s' host='%s' password='%s'" % (database, username, host, password)

# --------------- Main handler ------------------

def lambda_handler(event, context):
    print(event)
    # establish some variables

    # connect to database
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    print('connected to database')

    # get list of all tables in Database
    table_query = """SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"""
    cur.execute(table_query)
    all_tables = cur.fetchall()
    print('tables retrieved')

    # iterate tables
    types = ['index', 'frames', 'mosaic']
    features = []
    for table in all_tables:
        # get the service type from the suffix
        sfx = table[0].split("_")[-1]
        # build a name
        collection_name = table[0].replace('_' + sfx, '').replace('_', ' ').upper()
        # verify it is a service table
        if sfx in types:
            print(table[0])
            # get the records
            rec_query = "SELECT dl_orig, dl_georef, dl_index, ST_AsGeoJSON(geom) FROM %s" % table[0]
            cur.execute(rec_query)
            result = cur.fetchall()
            # iterate records in table
            for record in result:
                dl_orig = record[0]
                dl_georef = record[1]
                dl_index = record[2]
                # build geojson and add to feature list
                object = {
                    "geometry": json.loads(record[3]),
                    "type": "Feature",
                    "properties": {
                        "tablename": table[0],
                        "collection": collection_name,
                        "dl_orig": dl_orig,
                        "dl_georef": dl_georef,
                        "dl_index": dl_index
                    }
                }
                features.append(object)

    # write geojson locally in tmp folder
    feature_collection = FeatureCollection(features)
    tmp_file = '/tmp/compiled.geojson'
    with open('/tmp/compiled.geojson', 'w') as f:
        dump(feature_collection, f)
    print('tmp geojson written')

    # connect to s3 and upload geojson
    upload_key = 'geojson/compiled_historical_indexes.geojson'
    s3 = boto3.resource('s3')
    s3.Bucket(upload_bucket).upload_file(tmp_file,upload_key,ExtraArgs={'ACL':'public-read'})
    print("upload success!")

    # delete local geojson
    os.remove(tmp_file)
    print("local geojson deleted. /tmp clean.")

    # disconnect from Database
    conn.close()
    print('database connection closed.')

if __name__ == '__main__':
    lambda_handler(event='event', context='context')
