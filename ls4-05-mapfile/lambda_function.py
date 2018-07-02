# --------------- IMPORTS ---------------
import os
import boto3
import psycopg2

# Database Connection Info
database = os.environ.get('DB_NAME')
username = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
host = os.environ.get('DB_HOST')
port = os.environ.get('DB_PORT')
mapserver_access_key = os.environ.get('MAPSERVER_ACCESS_KEY_ID')
mapserver_secret_access_key = os.environ.get('MAPSERVER_SECRET_ACCESS_KEY')

conn_string = "dbname='%s' user='%s' host='%s' password='%s'" % (database, username, host, password)

# --------------- Main handler ------------------

def lambda_handler(event, context):
    print(event)
    # establish some variables
    print(event['Records'][0]['s3'])

    # prepare input event
    if 'sourceBucket' not in event.keys():
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        source_key = event['Records'][0]['s3']['object']['key']
        print('fired by event!')
        print(source_bucket, source_key)
    else:
        source_bucket = event['sourceBucket']
        source_key = event['sourceKey']

    # verify input is a cog
    if 'cog/tile_index/' not in source_key:
        print("source key is not a cog tile index! exiting...")
        print(source_key)
        return

    filename = source_key.split("/")[-1]
    collection = filename.replace('.shp', '')
    print("collection: %s" % collection)
    mapname = collection.upper().replace("_", "")
    print("mapname: %s" % mapname)
    wmstitle = collection.replace('_', ' ').title()
    print("wmstitle: %s" % wmstitle)
    tablename = collection.lower()
    print("tablename: %s" % tablename)

    # connect to database
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    # get extent (comes back as string)
    extent_query = "SELECT ST_Extent(geom) FROM %s;" % tablename
    print(extent_query)
    cur.execute(extent_query)
    response = cur.fetchone()
    box_string = response[0]
    print(response)
    # get the coordinates from the query and format as needed
    coords_string = box_string[(box_string.find('(') + 1):box_string.find(')')]
    mins = coords_string.split(",")[0]
    maxs = coords_string.split(",")[1]
    xmin = str(int(float(mins.split(" ")[0])) - 50)
    ymin = str(int(float(mins.split(" ")[1])) - 50)
    xmax = str(int(float(maxs.split(" ")[0])) + 50)
    ymax = str(int(float(maxs.split(" ")[1])) + 50)
    print("extent coordinates found!")
    print(xmin, ymin, xmax, ymax)

    # load up template mapfile
    with open('template.map') as template:
        t = template.read()
    print('template opened')

    # write new mapfile in /tmp
    mapfile = tablename + '.map'
    print('writing %s' % mapfile)
    with open('/tmp/' + mapfile, 'w') as m:
        t = t.replace('<database>', database)
        t = t.replace('<username>', username)
        t = t.replace('<password>', password)
        t = t.replace('<host>', host)
        t = t.replace('<port>', port)
        t = t.replace('<mapserver_access_key>', mapserver_access_key)
        t = t.replace('<mapserver_secret_access_key>', mapserver_secret_access_key)
        t = t.replace('<collection>', collection)
        t = t.replace('<mapname>', mapname)
        t = t.replace('<wmstitle>', wmstitle)
        t = t.replace('<tablename>', tablename)
        t = t.replace('<xmin>', xmin)
        t = t.replace('<ymin>', ymin)
        t = t.replace('<xmax>', xmax)
        t = t.replace('<ymax>', ymax)
        m.write(t)
    print('mapfile written')

    # connect to s3 and upload mapfile
    upload_key = 'mapfiles/%s' % mapfile
    s3 = boto3.resource('s3')
    s3.Bucket(source_bucket).upload_file('/tmp/' + mapfile,upload_key,ExtraArgs={'Metadata':{'mode':'33204','uid':'500','gid':'500','mtime':'1528814551'}})
    print("upload success!")

    # delete local mapfile
    os.remove('/tmp/' + mapfile)
    print("local mapfile deleted. /tmp clean.")

    # disconnect from Database
    conn.close()
    print('database connection closed.')

if __name__ == '__main__':
    lambda_handler(event='event', context='context')
