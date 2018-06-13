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
    console.log(event.Records[0].s3);
    // If not invoked directly then treat as coming from S3
    if (!event.sourceBucket) {
        if (event.Records[0].s3.bucket.name) {
    	   var sourceBucket = event.Records[0].s3.bucket.name;
    	   var sourceKey = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, ' '));
    	}
        else {
           console.error ('no source bucket defined');
        }
    }
    else {
        var sourceBucket = event.sourceBucket;
        var sourceKey =  event.sourceKey;
    }

    // escape if s3 event triggered by scanned upload or cog output
    if (!sourceKey.includes('/georef/')) {
      console.log("error: key doesn't include '/georef/'. exiting...");
      console.log(sourceKey);
      return
    }
    else if (sourceKey.includes(process.env.georefSubDir)) {
      console.log("error: key includes the 'georefSubDir' env variable. exiting...");
      console.log(sourceKey);
      return
    }
    else {
      // in case of s3 event triggered by a new overview file  we need to point
      // at the intermediate tif file not ovr
      // if (sourceKey.includes(".ovr")) {
      //    sourceKey = sourceKey.replace('.ovr','');
      //    console.log ('Stripped .ovr from key');
      // }

      console.log('Source Bucket: ' + sourceBucket);
      console.log('Source Key: ' + sourceKey);

      console.log('GDAL Args: ' + process.env.gdalArgs);
      console.log('ncBands: ' + process.env.ncBands);
      console.log('bwBands: ' + process.env.bwBands);

      console.log('Upload Bucket: ' + process.env.uploadBucket);
      console.log('Upload Key ACL: ' + process.env.uploadKeyAcl);
      console.log('Upload Georef Sub Directory: ' + process.env.georefSubDir);

      // adjust gdal command for number of bands in raster. if not bw or nc, just escape
      var bandCmd;
      if (sourceKey.includes('bw/')) {
        bandCmd = process.env.bwBands + " ";
      }
      else if (sourceKey.includes('nc/')) {
        bandCmd = process.env.ncBands + " ";
      }
      else {
        console.log("error: key doesn't include 'bw/' or 'nc/'. exiting...");
        return
      }

      const cmd = 'AWS_REQUEST_PAYER=requester'
          + ' GDAL_DISABLE_READDIR_ON_OPEN=YES CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif ./bin/gdal_translate '
          + bandCmd + process.env.gdalArgs
          + ' /vsis3/' + sourceBucket + '/' + sourceKey + ' /tmp/output.tif';
      console.log('Command to run: ' + cmd);

      // clear contents of tmp dir in case of reuse
      console.log(systemSync('rm -fv /tmp/*'));
      // run command here should have some error checking
      console.log(systemSync(cmd));
      console.log(systemSync('ls -alh /tmp'));

      // default upload key is same as the source key with added georef sub Directory
      var srcKeyParts = sourceKey.split("/");
      var filename = srcKeyParts[srcKeyParts.length-1];
      var fileWithSubDir = process.env.georefSubDir + filename;
      var uploadKey = sourceKey.replace(filename, fileWithSubDir);
      console.log('uploadKey: ' + uploadKey);

      var body = fs.createReadStream('/tmp/output.tif');

      // when writing to your own bucket 'authenticated-read'
      // or
      // when writing to another account's bucket 'bucket-owner-full-control'
      var s3obj = new aws.S3({params: {Bucket: process.env.uploadBucket,
          Key: uploadKey,
          ACL: process.env.uploadKeyAcl,
          ContentType: 'image/tiff'
      }});

      // upload output of the gdal util to S3
      s3obj.upload({Body: body})
          .on('httpUploadProgress', function(evt) {
              //console.log(evt);
              })
          .send(function(err, data) {callback(err, 'Process complete!');}
      )
    }
};
