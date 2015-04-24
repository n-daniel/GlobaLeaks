importScripts("/components/scrypt/index.js");

scrypt_hash = function(password, rounds, salt, scrypt) {
  var utf8_pwd = scrypt.encode_utf8(password);
  var bytearray_pwd = scrypt.crypto_scrypt(utf8_pwd, salt, rounds, 8, 1, 16);
  return scrypt.to_hex(bytearray_pwd);
}

onmessage = function(e) {
  var password = e.data[0];
  var rounds = e.data[1];
  var salt = e.data[2];

  var scrypt = scrypt_module_factory(33554432);
  var key = scrypt_hash(password, rounds, salt, scrypt);

  postMessage(key);
}
