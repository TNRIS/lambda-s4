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

    // in case of s3 event triggered by a new overview file (which it should if
    // wired correctly) we need to point at the intermediate tif file not ovr
    if (sourceKey.includes(".ovr")) {
       sourceKey = sourceKey.replace('.ovr','');
       console.log ('Stripped .ovr from key');
    }

    // escape if s3 event triggered by upload not in georef subdirectory
    var deepDirectory = 'georef/' + process.env.georefSubDir;
    if (!sourceKey.includes(deepDirectory)) {
      console.log("error: key doesn't include '" + deepDirectory + "'. exiting...");
      console.log(sourceKey);
      return
    }
    else {

      console.log('Source Bucket: ' + sourceBucket);
      console.log('Source Key: ' + sourceKey);
      console.log('NC GDAL Args: ' + process.env.ncGdalArgs);
      console.log('BW GDAL Args: ' + process.env.bwGdalArgs);

      console.log('Upload Bucket: ' + process.env.uploadBucket);
      console.log('Upload Key ACL: ' + process.env.uploadKeyAcl);
      console.log('Upload Georef Sub Directory: ' + process.env.georefSubDir);

      // choose gdal command for number of bands in raster. if not bw or nc, just escape
      var gdalCmd;
      if (sourceKey.includes('bw/')) {
        gdalCmd = process.env.bwGdalArgs;
      }
      else if (sourceKey.includes('nc/')) {
        gdalCmd = process.env.ncGdalArgs;
      }
      else {
        console.log("error: key doesn't include 'bw/' or 'nc/'. exiting...");
        return
      }

      // the AWS access keys will not be neccessary in gdal ver 2.3 due to IAM Role support
      const cmd = 'AWS_REQUEST_PAYER=requester'
          + ' GDAL_DISABLE_READDIR_ON_OPEN=YES CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif ./bin/gdal_translate '
          + gdalCmd
          + ' /vsis3/' + sourceBucket + '/' + sourceKey + ' /tmp/output.tif';
      console.log('Command to run: ' + cmd);

      // clear contents of tmp dir in case of reuse
      console.log(systemSync('rm -fv /tmp/*'));
      // run command here should have some error checking
      console.log(systemSync(cmd));
      console.log(systemSync('ls -alh /tmp'));

      // upload key is source key swapped with georef & sub swapped for COG
      var uploadKey = sourceKey.replace(deepDirectory, 'cog/');
      console.log('uploadKey: ' + uploadKey);

      var body = fs.createReadStream('/tmp/output.tif');

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
          .send(function(err, data) {
            console.log(data);
            const payload = {sourceBucket: process.env.uploadBucket,sourceKey: uploadKey}
            lambda.invoke({
              ClientContext: "ls4-03",
              FunctionName: "ls4-04-shp_index",
              InvocationType: "Event",
              Payload: JSON.stringify(payload) // pass params
            }, function(error, data) {
              if (error) {
                context.done('error', error);
              }
              if(data.Payload){
                console.log("ls4-04-shp_index invoked!")
                context.succeed(data.Payload)
              }
            });
            callback(err, 'Process complete!');}
      )
    }
};
