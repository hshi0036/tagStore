var BucketName = "bucket-s3a2";
var bucketRegion = "us-east-1";
var poolId = "us-east-1:4e6caeff-e4ad-47cf-b632-d939bd897b01"


AWS.config.update({
  region: bucketRegion,
  credentials: new AWS.CognitoIdentityCredentials({
      IdentityPoolId: poolId
  })
});

var s3 = new AWS.S3({
    apiVersion: '2006-03-01',
    params: {Bucket: BucketName}
});




function upload() {
  var files = document.getElementById("photoupload").files;
  if (!files.length) {
    return alert("Please choose a file to upload first.");
  }
  var file = files[0];
  var fileName = file.name;
  // var albumPhotosKey = encodeURIComponent(albumName) + "//";
  var fileUrl = 'https://' + bucketRegion + '.amazonaws.com/' +  fileName;

  // Use S3 ManagedUpload class as it supports multipart uploads
  s3.upload({
      Key: fileName,
      Body: file,
      ACL: "public-read"
  }, function(err, data) {
     if(err) {
        reject('error');
        }
        alert('Successfully Uploaded!');
      });
  // var promise = upload.promise();

  // promise.then(
  //   function(data) {
  //     alert("Successfully uploaded photo.");
  //   },
  //   function(err) {
  //     return alert("There was an error uploading your photo: ", err.message);
  //   }
  // );
}