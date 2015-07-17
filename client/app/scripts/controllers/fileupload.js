GLClient.controller('WBFileUploadCtrl', ['$scope', 'Authentication', function($scope, Authentication) {

  function encryptedFileStream() {
    this.read_function = 'slice';

    this.buffers = [];
    this.buffered_total = 0;

    this.readStartPointer = 0;
    this.readEndPointer = 0;
  };

  $scope.efs = new encryptedFileStream();
  $scope.chunk = null;
  $scope.neededBytes = 0;

  var initFileFn = function(fileObj) {
    $scope.efs.file = fileObj.file;
    console.log(fileObj.file);

    if ($scope.efs.file.slice)
      $scope.efs.read_function = 'slice';
    else if ($scope.efs.file.mozSlice)
      $scope.efs.read_function = 'mozSlice';
    else if ($scope.efs.file.webkitSlice)
      $scope.efs.read_function = 'webkitSlice';

    console.log($scope.efs.read_function);

    $scope.efs.origFileSize = $scope.efs.file.size;
    console.log($scope.efs.origFileSize);

    $scope.efs.message_stream = new openpgp.stream.MessageStream($scope.submission.receiversAndWbKeys,
                                                                 $scope.efs.origFileSize,
                                                                 'msg.txt',
                                                                 {encoding: 'binary'});

    fileObj.size = $scope.efs.message_stream.size - 1; // make flow know the final encrypted file size!

    var onDataCallback = function(d) {
      if (d.length) {
        $scope.efs.buffers.push(d);
        $scope.efs.buffered_total += d.length;
      }
    
      if ($scope.chunk && $scope.efs.buffered_total >= $scope.neededBytes) {
        var buffer = new Uint8Array($scope.neededBytes);
        var missing = $scope.neededBytes;
        var _chunk = $scope.chunk;
        $scope.chunk = null;
        $scope.neededBytes = 0;

        var offset = 0;
        for (var i = 0; i < $scope.efs.buffers.length; i++) {
          var copy_length = $scope.efs.buffers[i].length >= missing ? missing : $scope.efs.buffers[i].length;
          buffer.set($scope.efs.buffers[i].subarray(0, copy_length), offset);
          offset += copy_length;
          missing -= copy_length;
          $scope.efs.buffered_total -= copy_length;
          if (missing === 0) {
            if (copy_length != $scope.efs.buffers[i].length) {
              $scope.efs.buffers[i] = $scope.efs.buffers[i].subarray(copy_length);
              $scope.efs.buffers = $scope.efs.buffers.slice(i);
            } else {
              $scope.efs.buffers = $scope.efs.buffers.slice(i + 1);
            }
            _chunk.readFinished(new Blob([buffer.buffer]));
            break;
          }
        }
      }
    };

    $scope.efs.message_stream.setOnDataCallback(onDataCallback);

  }

  var _readFileFn = function(fileObj, startByte, endByte, fileType, chunk) {
    var reader = new FileReader();

    reader.onloadend = function(e) {
      if (reader.result) {
        var data = new Uint8Array(reader.result);
        $scope.efs.message_stream.write(data);
        if ($scope.efs.readEndPointer === $scope.efs.origFileSize) {
          $scope.efs.message_stream.end();
        }
      }
    }

    reader.readAsArrayBuffer($scope.efs.file[$scope.efs.read_function]($scope.efs.readStartPointer,
                                                                       $scope.efs.readEndPointer,
                                                                       fileType));
  }

  var readFileFn = function(fileObj, startByte, endByte, fileType, chunk) {
    $scope.neededBytes = (endByte - startByte);
    $scope.chunk = chunk;

    $scope.efs.readStartPointer = $scope.efs.readEndPointer;
    $scope.efs.readEndPointer = $scope.efs.readStartPointer + $scope.neededBytes;
    if ($scope.efs.readEndPointer > $scope.efs.origFileSize) {
      $scope.efs.readEndPointer = $scope.efs.origFileSize;
    }
    if ($scope.efs.readStartPointer != $scope.efs.readEndPointer) {
      _readFileFn(fileObj, $scope.efs.readStartPointer, $scope.efs.readEndPointer, fileType, chunk);
    } else {
      onDataCallback([]);
    }
  }

  $scope.$on('flow::fileAdded', function(event, $flow, flowFile) {
    flowFile.done = false;
    $scope.uploads.push(flowFile);

    if (flowFile.size > $scope.node.maximum_filesize * 1024 * 1024) {
      flowFile.error = true;
      flowFile.error_msg = "This file exceeds the maximum upload size for this server.";
      flowFile.done = true;
      event.preventDefault();
    }

    angular.forEach($scope.upload_callbacks, function(callback) {
      callback();
    });
  });

  $scope.$on('flow::fileSuccess', function(event, $flow, flowFile) {
    var arrayLength = $scope.uploads.length;
    for (var i = 0; i < arrayLength; i++) {
      if ($scope.uploads[i].uniqueIdentifier === flowFile.uniqueIdentifier) {
        $scope.uploads[i].done = true;
      }
    }

    angular.forEach($scope.upload_callbacks, function(callback) {
      callback();
    });

  });

  $scope.flow_init = {
    target: $scope.fileupload_url,
    headers: $scope.get_auth_headers(),
    initFileFn: initFileFn,
    readFileFn: readFileFn
  }

}]);
