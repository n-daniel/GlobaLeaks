GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope) {

  function encryptedFileStream(file, pub_keys) {
    this.file = file;

    this.message_stream = new openpgp.stream.MessageStream(pub_keys,
                                                           file.size,
                                                           file.name);

    this.buffer = new Uint8Array(0);
  };

  encryptedFileStream.prototype.read = function(chunk, startByte, endByte, fileType) {
    var neededBytes = (endByte - startByte),
      self = this,
      reader = new FileReader(),
      file = chunk.fileObj.file;

    self.message_stream.setOnDataCallback(function(d) {
      var tmp = new Uint8Array(self.buffer.length + d.length);
      tmp.set(self.buffer, 0);
      tmp.set(d, self.buffer.length);
      self.buffer = tmp;

      if (neededBytes <= self.buffer.length) {
        var data = self.buffer.subarray(0, neededBytes);
        self.buffer = self.buffer.subarray(neededBytes, self.buffer.length);
        chunk.readFinished(data);
      }
    });

    reader.onloadend = function(e) {
      if (reader.result) {
        console.log(reader.result);
        self.message_stream.write(reader.result);
        if (endByte === file.size) {
          self.message_stream.end();
        }
      }
    }

    var function_name = 'slice';

    if (file.slice)
      function_name = 'slice';
    else if (file.mozSlice)
      function_name = 'mozSlice';
    else if (file.webkitSlice)
      function_name = 'webkitSlice';

    reader.readAsBinaryString(file[function_name](startByte, 
                                                  startByte + neededBytes,
                                                  fileType));
  };

  $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
    flowFile.done = false;
    $scope.uploads.push(flowFile);

    if (flowFile.size > $scope.node.maximum_filesize * 1024 * 1024) {
      flowFile.error = true;
      flowFile.error_msg = "This file exceeds the maximum upload size for this server.";
      flowFile.done = true;
      event.preventDefault();
    }

    angular.forEach($scope.upload_callbacks, function (callback) {
      callback();
    });
  });

  $scope.$on('flow::fileSuccess', function (event, $flow, flowFile) {
    var arrayLength = $scope.uploads.length;
    for (var i = 0; i < arrayLength; i++) {
      if ($scope.uploads[i].uniqueIdentifier === flowFile.uniqueIdentifier) {
        $scope.uploads[i].done = true;
      }
    }

    angular.forEach($scope.upload_callbacks, function (callback) {
      callback();
    });

  });

  $scope.flow_init = {
    target: $scope.fileupload_url,
    headers: $scope.get_auth_headers(),
    preprocess: function(chunk) {
      var encrypted_file_stream = new encryptedFileStream(chunk.fileObj, $scope.submission.receiversAndWbKeys);
      chunk.fileObj.encrypted_file_stream = encrypted_file_stream;
      console.log(encrypted_file_stream.message_stream.size);
      chunk.fileObj.size = encrypted_file_stream.message_stream.size;
      chunk.preprocessFinished();
    },
    read: function(chunk, startByte, endByte, fileType) {
      chunk.fileObj.encrypted_file_stream.read(chunk, startByte, endByte, fileType);
    }
  }

}]);
