importScripts('openpgp.worker.js');
importScripts('scrypt.js');
 
var generateKeyPair = window.openpgp.generateKeyPair;

window.openpgp.generateKeyPair = function(options) {

  function DeterministicSeed(receipt, salt) {
    var self = this;

    scrypt = scrypt_module_factory(33554432);
    pwd = scrypt.encode_utf8(options.receipt);

    self.seed = scrypt.crypto_scrypt(pwd, salt, 4096, 8, 1, 128 * 2);
    self.offset = 0;

    function nextBytes(byteArray) {
      for (var n = 0; n < byteArray.length; n++) {
        byteArray[n] = self.seed[self.offset++ % self.seed.length];
      }
    }

    this.nextBytes = nextBytes;
  }

  options.prng = new DeterministicSeed(options.receipt, options.salt);
 
  return generateKeyPair(options);
}
