// this function is meant to be run from an S3 object creation event.
// It runs when a tif file lands in the bucket, reading the file and generating an ovr file which puts back in the same bucket.
var aws = require('aws-sdk');
var s3 = new aws.S3();
const exec = require('child_process').execSync;
const fs = require('fs');

// runs executable synchronously and camptures stdout to srting
function systemSync(cmd) {
    return exec(cmd).toString();
};

exports.handler = function(event, context, callback) {
    //grab bucket name and key from put event coming from S3
    const sourceBucket = event.sourceBucket;
    const sourceKey = decodeURIComponent(event.sourceKey.replace(/\+/g, ' '));

    if (!sourceKey.includes(process.env.georefSubDir)) {
      console.log("error: key doesn't include the 'georefSubDir' env variable. exiting...");
      console.log(sourceKey);
      return
    }
    else {

      console.log('Source Bucket: ' + sourceBucket);
      console.log('Source Key: ' + sourceKey);
      console.log('gdaladdo Args: ' + process.env.gdaladdoArgs);
      console.log('gdaladdo Layers: ' + process.env.gdaladdoLayers);
      console.log('uploadBucket: ' + process.env.uploadBucket);
      console.log('Upload Georef Sub Directory: ' + process.env.georefSubDir);

      console.log(systemSync('ls -alh /tmp'));
      // remove in case any file is there from previous run
      console.log(systemSync('rm -fv /tmp/*'));

      var inputStream = fs.createWriteStream('/tmp/input.tif');
      s3.getObject({Bucket: sourceBucket, Key: sourceKey, RequestPayer: 'requester'})
        .createReadStream()
        .pipe(inputStream)
        .on('finish', function() {
            inputStream.end;
            var gdalParams = './bin/gdaladdo '
            + process.env.gdaladdoArgs
            + ' /tmp/input.tif ' + process.env.gdaladdoLayers;
            console.log('gdalParams: ' + gdalParams);

            // run gdaladdo
            console.log(systemSync(gdalParams));
            console.log(systemSync('ls -alh /tmp'));
     
        	  // upload key should be same as source key name, other than the .ovr extension
        	  var uploadKey = sourceKey;

            // more efficient to use -ro to create an overview sidecar rather than add it to the source
            // the ovr file is smaller to write back next to the source tif in S3.
            if (process.env.gdaladdoArgs.includes("-ro")) {
                var body = fs.createReadStream('/tmp/input.tif.ovr');
                uploadKey = uploadKey + '.ovr';
            } else {
                var body = fs.createReadStream('/tmp/input.tif');
            }

            console.log('uploadKey: ' + uploadKey);

            var s3obj = new aws.S3({params: {Bucket:  process.env.uploadBucket, Key: uploadKey, ACL:'authenticated-read'}});
            s3obj.upload({Body: body})
              .on('httpUploadProgress', function(evt) {
  		        //console.log(evt);
  		        })
              .send(function(err, data) {callback(err, 'Process complete!');});
       })
     }
};
