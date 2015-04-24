importScripts("/components/scrypt/index.js");

generate_deterministic_seed = function(receipt) {
    scrypt = scrypt_module_factory(33554432),
    utf8_pwd = scrypt.encode_utf8(receipt),
    salt = "This is the salt.";
    var seed = scrypt.crypto_scrypt(utf8_pwd, salt, 4096,
                                           8, 1, 128 * 2);
    return seed;
}

onmessage = function(e) {
  var receipt = e.data[0];
  var seed = generate_deterministic_seed(receipt);
  postMessage(seed);
}


