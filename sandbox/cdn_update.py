
import psycopg2

# Database Connection Info
database = ''
username = ''
password = ''
host = ''
port = ####

conn_string = "dbname='%s' user='%s' host='%s' password='%s' port='%s'" % (database, username, host, password, port)

def lambda_handler(event, context):
    print(conn_string)
    # connect to database
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    print('connected')
    try:
        # retrieve list of tables
        cur.execute("""SELECT table_name FROM information_schema.tables
               WHERE table_schema = 'public'""")
        default_tables = ['geography_columns', 'geometry_columns', 'spatial_ref_sys', 'raster_columns', 'raster_overviews']
        tables = [x[0] for x in cur.fetchall() if x[0] not in default_tables]
        # tables = [x[0] for x in cur.fetchall() if '_index' in x[0]]

        # print("RDS tables:")
        # print(tables)
        print('length', len(tables))
        del cur
        for t in tables:
            # print(t)
            cur = conn.cursor()
            # cur.execute("SELECT * FROM %s" % t)
            # res = cur.fetchall()
            # for r in res:
            #     print(r)
            print(t)
            cur.execute("""
            UPDATE %s
            SET dl_orig = REPLACE(dl_orig, 'https://s3.amazonaws.com/tnris-ls4/', 'https://cdn.tnris.org/'),
            dl_georef = REPLACE(dl_georef, 'https://s3.amazonaws.com/tnris-ls4/', 'https://cdn.tnris.org/'),
            dl_index = REPLACE(dl_index, 'https://s3.amazonaws.com/tnris-ls4/', 'https://cdn.tnris.org/'); """ % (t))
            conn.commit()
            del cur

    except Exception as e:
        print("there was an error.")
        print(e)

    # disconnect from Database
    conn.close()
    print('database connection closed.')

if __name__ == '__main__':
    print('starting')
    lambda_handler(event='event', context='context')
