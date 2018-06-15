'use strict';
//
const child_process = require('child_process');
const aws = require('aws-sdk');
const s3 = new aws.S3();
const exec = require('child_process').execSync;
const fs = require('fs');

function systemSync(cmd) {
    return exec(cmd).toString();
};

exports.handler = (event, context, callback) => {
    //grab bucket name and key from put event coming from S3
    const sourceBucket = event.sourceBucket;
    const sourceKey = decodeURIComponent(event.sourceKey.replace(/\+/g, ' '));

    // escape if s3 event triggered by upload not in georef subdirectory
    if (!sourceKey.includes('/cog/')) {
      console.log("error: key doesn't include '/cog/'. exiting...");
      console.log(sourceKey);
      return
    }
    else {
      console.log('Source Bucket: ' + sourceBucket);
      console.log('Source Key: ' + sourceKey);
      // console.log('NC GDAL Args: ' + process.env.ncGdalArgs);
      // console.log('BW GDAL Args: ' + process.env.bwGdalArgs);
      //
      // console.log('Upload Bucket: ' + process.env.uploadBucket);
      // console.log('Upload Key ACL: ' + process.env.uploadKeyAcl);
      // default upload key is same as the source key with added georef sub Directory
      var srcKeyParts = sourceKey.split("/");
      var filename = srcKeyParts[srcKeyParts.length-1];
      var cogFolderKey = sourceKey.replace(filename, '');
      console.log('cogFolderKey: ' + cogFolderKey);

      var cogsList = "";
      function listKeys(nextToken) {
        var params = {
          Bucket: sourceBucket,
          Prefix: cogFolderKey
        }
        if (nextToken != '') {
          params['ContinuationToken'] = nextToken;
        }

        console.log(params);
        s3.listObjectsV2(params, function(err, data) {
          if (err) {
            console.log(err, err.stack);
          }
          else {
            data.Contents.forEach(function(c) {
              cogsList += "/vsis3/" + sourceBucket + "/" + c.Key + " "
            })

            if (data.IsTruncated) {
              console.log("there's more... let's go get them!");
              listKeys(data.NextContinuationToken);
            }
            else {
              console.log(cogsList);
              // the AWS access keys will not be neccessary in gdal ver 2.3 due to IAM Role support
              const cmd = './bin/gdaltindex -src_srs_name src_srs /tmp/output.shp '
                  + cogsList;
              console.log('Command to run: ' + cmd);

              // clear contents of tmp dir in case of reuse
              console.log(systemSync('rm -fv /tmp/*'));
              // run command here should have some error checking
              console.log(systemSync(cmd));
              console.log(systemSync('ls -alh /tmp'));
              console.log(systemSync('ls /tmp'));
            }
          }
        });
      }
      listKeys('');


      //
      // // upload key is source key swapped with georef & sub swapped for COG
      // var uploadKey = sourceKey.replace(deepDirectory, 'cog/');
      // console.log('uploadKey: ' + uploadKey);
      //
      // var body = fs.createReadStream('/tmp/output.tif');
      //
      // var s3obj = new aws.S3({params: {Bucket: process.env.uploadBucket,
      //     Key: uploadKey,
      //     ACL: process.env.uploadKeyAcl,
      //     ContentType: 'image/tiff'
      // }});
      //
      // // upload output of the gdal util to S3
      // s3obj.upload({Body: body})
      //     .on('httpUploadProgress', function(evt) {
      //         //console.log(evt);
      //         })
      //     .send(function(err, data) {callback(err, 'Process complete!');}
      // )
    }
};
