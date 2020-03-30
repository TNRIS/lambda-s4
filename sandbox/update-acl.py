import boto3

client = boto3.client('s3')
q_bucket = 'tnris-public-data'


if q_bucket != '':

    def q_run(ct=None, loop=0):
        print('loop: ' + str(loop))
        if ct is None:
            response = client.list_objects_v2(
                Bucket=q_bucket,
                Prefix='prod-historic/'
            )
        else:
            response = client.list_objects_v2(
                Bucket=q_bucket,
                Prefix='prod-historic/',
                ContinuationToken=ct
            )
        for c in response['Contents']:
            key = c['Key']
            print(key)
            acl_res = client.put_object_acl(
                ACL='public-read',
                Bucket=q_bucket,
                Key=key
            )
                
        loop += 1
        if response['IsTruncated'] is True:
            q_run(response['NextContinuationToken'], loop)
        else:
            print('no more loops!')
            return 

    q_run()
 
else:
    print('bucket not declared. populate variables and try again.')


print("that's all folks!!")