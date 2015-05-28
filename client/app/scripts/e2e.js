angular.module('e2e', []).
  factory('glcrypto', ['$q', function($q) {
    var scrypt = function(password,
                          salt,
                          logN,
                          encoding) {
      var defer = $q.defer();

      var worker = new Worker('/scripts/crypto/scrypt-async.worker.js');

      worker.onmessage = function(e) {
        defer.resolve(e.data);
        worker.terminate();
      };

      worker.postMessage({
        password: password,
        salt: salt,
        logN: logN,
        r: 8,
        dkLen: 256,
        encoding: encoding
      });

      return defer.promise;
    }

    var e2e_key_bits = 2048;
    var pgp_key_bits = 4096;

    return {
      scrypt: function(data, salt, logN) {
        var defer = $q.defer();

        scrypt(data, salt, logN, 'hex').then(function(stretched) {
          defer.resolve({
            value: data,
            stretched: stretched
          });
        });

        return defer.promise;
      },
      
      derivate_password: function(user_password, salt) {
        return this.scrypt(user_password, salt, 12);
      },

      derivate_passphrase: function(user_password, salt) {
        return this.scrypt(user_password, salt, 13);
      },

      derivate_keycode: function(keycode, salt) {
        return this.scrypt(keycode, salt, 12);
      },
      derivate_user_password: function (user_password, salt) {
        var defer = $q.defer();

        nested = this;

        this.derivate_password(user_password, salt).then(function(password) {
          this.scrypt = nested.scrypt;
          this.derivate_passphrase = nested.derivate_passphrase;
          this.derivate_passphrase(user_password, salt).then(function(passphrase) {
            defer.resolve({password: password.stretched, passphrase: passphrase.stretched});
          });
        });

        return defer.promise;
      },
      generate_e2e_key: function (user_password, salt) {
        var defer = $q.defer();
        var password;
        var passphrase;

        this.derivate_user_password(user_password, salt).then(function(data) {
          var key_options = {
            userId: 'randomuser@globaleaks.org',
            passphrase: data.passphrase,
            numBits: e2e_key_bits
          }

          var key = openpgp.generateKeyPair(key_options).then(function(keyPair) {
            defer.resolve({
              password: data.password,
              passphrase: data.passphrase,
              e2e_key_pub: keyPair.publicKeyArmored,
              e2e_key_prv: keyPair.privateKeyArmored
            });
          });
        });

        return defer.promise;
      },
      generate_keycode: function() {
        var keycode = '';
        for (var i=0; i<16; i++) {
          keycode += openpgp.crypto.random.getSecureRandom(0, 9);
        }
        return keycode;
      },
      generate_key_from_keycode: function(keycode, salt) {
        var defer = $q.defer();

        var workerAvailable = openpgp.initWorker('/scripts/crypto/ww_whistleblower_deterministic_key.js');

        openpgp.getWorker().generateKeyPair({
          numBits: 2048,
          userId: "randomuser@globaleaks.org",
          unlocked: true,
          created: new Date(42),
          salt: salt,
          keycode: keycode
        }).then(function(keyPair){
          keyPair.key.primaryKey.created = new Date(42);
          keyPair.key.subKeys[0].subKey.created = new Date(42);
          defer.resolve(keyPair);
        });

        return defer.promise;
      },
      generate_pgp_key: function(user_email, passphrase) {
        var key_options = {
          userId: user_email,
          passphrase: passphrase,
          numBits: pgp_key_bits
        }

        var key = openpgp.generateKeyPair(key_options).then(function(keyPair) {
          defer.resolve({
            pgp_key_pub: keyPair.publicKeyArmored,
            pgp_key_prv: keyPair.privateKeyArmored
          });
        });
      }
    }
}]);
