importScripts('scrypt-async.min.js');
importScripts('openpgp.worker.min.js');
 
var generateKeyPair = window.openpgp.generateKeyPair;

window.openpgp.generateKeyPair = function(options) {

  function DeterministicSeed(seed) {
    var self = this;

    self.seed = seed;
    self.offset = 0;

    function nextBytes(byteArray) {
      for (var n = 0; n < byteArray.length; n++) {
        byteArray[n] = self.seed[self.offset++ % self.seed.length];
      }
    }

    this.nextBytes = nextBytes;
  }

  return new Promise(function(resolve, reject) {
    scrypt(options.keycode, options.salt, 12, 8, 256, function(result) {
      options.prng = new DeterministicSeed(result);
      generateKeyPair(options).then(function(result) {
        resolve(result);
      });
    });
  });
}
