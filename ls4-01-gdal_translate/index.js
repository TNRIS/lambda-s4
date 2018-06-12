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
    console.log(event);
    console.log(context);
    console.log(process.env);
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

    // in case of s3 event triggered by a new overview file  we need to point
    // at the intermediate tif file not ovr
    if (sourceKey.includes(".ovr")) {
       sourceKey = sourceKey.replace('.ovr','');
       console.log ('Stripped .ovr from key');
    }

    // console.log(JSON.stringify(event), null, 2);
    console.log('Source Bucket: ' + sourceBucket);
    console.log('Source Key: ' + sourceKey);
    console.log('GDAL Args: ' + process.env.gdalArgs);
    console.log('1st find value: ' + process.env.find01);
    console.log('1st replace value: ' + process.env.replace01);
    console.log('2nd find value: ' + process.env.find02);
    console.log('2nd replace value: ' + process.env.replace02);
    console.log('Upload Bucket: ' + process.env.uploadBucket);
    console.log('Upload Key ACL: ' + process.env.uploadKeyAcl);
    console.log('Upload Key Prefix: ' + process.env.uploadPrefix);

    //
    // // the AWS access keys will not be neccessary in gdal ver 2.3 due to IAM Role support
    // const cmd = 'AWS_REQUEST_PAYER=requester'
    //     + ' GDAL_DISABLE_READDIR_ON_OPEN=YES CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif ./bin/gdal_translate '
    //     + process.env.gdalArgs
    //     + ' /vsis3/' + sourceBucket + '/' + sourceKey + ' /tmp/output.tif';
    // console.log('Command to run: ' + cmd);
    //
    // // clear contents of tmp dir in case of reuse
    // console.log(systemSync('rm -fv /tmp/*'));
    // // run command here should have some error checking
    // console.log(systemSync(cmd));
    // console.log(systemSync('ls -alh /tmp'));
    //
    // // default upload key is same as the source key
    // var uploadKey = sourceKey;
    //
    // // typically when your are building COGS you want to modify parts of the key name.
    // // 1st find/replace pair
    // if (process.env.find01 && process.env.replace01) {
    //     var uploadKey = uploadKey.replace(process.env.find01, process.env.replace01);
    // }
    //
    // // 2nd find and replace pair
    // if (process.env.find02 && process.env.replace02) {
    //     var uploadKey = uploadKey.replace(process.env.find02, process.env.replace02);
    // }
    //
    // // mostly for testing. allows you modify root of key name.
    // if (process.env.uploadKeyPrefix) {
    //     var uploadKey = process.env.uploadKeyPrefix + '/' + uploadKey;
    // }
    // console.log('uploadKey: ' + uploadKey);
    //
    // var body = fs.createReadStream('/tmp/output.tif');
    //
    // // when writing to your own bucket 'authenticated-read'
    // // or
    // // when writing to another account's bucket 'bucket-owner-full-control'
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
};
