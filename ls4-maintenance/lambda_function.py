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
bucket_name = os.environ.get('BUCKET')
aws_account = os.environ.get('AWS_ACCOUNT')
sns_error_topic = os.environ.get('SNS_ERROR_TOPIC')

conn_string = "dbname='%s' user='%s' host='%s' password='%s'" % (database, username, host, password)
global_table_list = ''

# --------------- Main handler ------------------

def compare_mapfiles(client, tables, cur, token=''):
    # set aside global table list for inverse comparison
    if token == '':
        response = client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='mapfiles/'
        )
    else:
        response = client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='mapfiles/',
            ContinuationToken=token
        )
    # cleanup response to be list of keys
    keys = [x['Key'] for x in response['Contents'] if x['Key'] != 'mapfiles/']
    print(keys)

    for k in keys:
        # make sure only .map files in mapfiles/ s3 directory
        if k[-4:] != '.map':
            print(k + " is not a mapfile and shouldn't be in mapfiles/. Deleting.")
            response = client.delete_object(
                Bucket=bucket_name,
                Key=k
            )
            m = "%s is not a mapfile has been deleted." % (k)
            sns_error(m)
        # make sure each mapfile is a table in the database
        mapfile_name = k.replace("mapfiles/", "").replace(".map", "")
        if mapfile_name not in tables:
            print(mapfile_name + " is not a table in the rds database.")
            m = "%s is a mapfile in s3 but %s is not a table in the RDS database." % (k, mapfile_name)
            sns_error(m)
        else:
            # remove table name from list for inverse comparison
            global global_table_list
            global_table_list.remove(mapfile_name)

    if 'NextContinuationToken' in response.keys():
        compare_mapfiles(client, tables, cur, response['NextContinuationToken'])
    return

def excess_tables(conn, cur):
    # global_table_list is now a list of tables without mapfiles
    # lets notify they are excess and delete
    print('excess')
    print(global_table_list)
    for t in global_table_list:
        print(t + " is an RDS table but doesn't have a mapfile. Deleting.")
        query = 'DROP TABLE "%s";' % (t)
        cur.execute(query)
        conn.commit()
        m = t + " was an RDS table without a mapfile and has been deleted."
        sns_error(m)
    return

def sns_error(m):
    # publish message to the project SNS topic
    sns = boto3.resource('sns')
    arn = 'arn:aws:sns:us-east-1:%s:%s' % (aws_account, sns_error_topic)
    topic = sns.Topic(arn)
    response = topic.publish(
        Message=m,
        Subject='LS4 Maintenance Error Notification'
    )
    print('sns error message dispatched.')
    return

def lambda_handler(event, context):
    # global clients
    client = boto3.client('s3')

    # connect to database
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    try:
        # retrieve list of tables
        cur.execute("""SELECT table_name FROM information_schema.tables
               WHERE table_schema = 'public'""")
        default_tables = ['geography_columns', 'geometry_columns', 'spatial_ref_sys', 'raster_columns', 'raster_overviews']
        tables = [x[0] for x in cur.fetchall() if x[0] not in default_tables]
        global global_table_list
        global_table_list = tables
        print(tables)

        # compare table list to mapfiles in bucket
        compare_mapfiles(client, tables, cur)
        # now we can do the inverse table name comparison
        excess_tables(conn, cur)

    except Exception as e:
        print("there was an error.")
        print(e)

    # disconnect from Database
    conn.close()
    print('database connection closed.')

if __name__ == '__main__':
    lambda_handler(event='event', context='context')
