import sys
import os
import base64

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes


class Files:
    def __init__(self):
        self.in_name = 'plain.txt'
        self.cipher_name = 'rsa_cipher.bin'
        self.cipher_b64_name = 'rsa_cipher.b64'
        self.dec_name = 'rsa_dec.txt'
        self.priv_name = 'rsa_priv.pem'
        self.pub_name = 'rsa_pub.pem'
        self.log_name = 'log.txt'
    def read_plain(self):
        if not os.path.exists(self.in_name):
            s = 'ПОЗНАЙ СЕБЯ'
            with open(self.in_name, 'w', encoding='utf-8') as f:
                f.write(s)
        with open(self.in_name, 'rb') as f:
            return f.read()
    def write_cipher(self, b):
        with open(self.cipher_name, 'wb') as f:
            f.write(b)
    def write_cipher_b64(self, b):
        with open(self.cipher_b64_name, 'wb') as f:
            f.write(base64.b64encode(b))
    def write_dec(self, b):
        with open(self.dec_name, 'wb') as f:
            f.write(b)
    def write_priv(self, b):
        with open(self.priv_name, 'wb') as f:
            f.write(b)
    def write_pub(self, b):
        with open(self.pub_name, 'wb') as f:
            f.write(b)
    def load_priv(self):
        if not os.path.exists(self.priv_name):
            return None
        with open(self.priv_name, 'rb') as f:
            return f.read()
    def load_pub(self):
        if not os.path.exists(self.pub_name):
            return None
        with open(self.pub_name, 'rb') as f:
            return f.read()
    def open_log(self):
        return open(self.log_name, 'a', encoding='utf-8')

class Tee:
    def __init__(self, orig, f):
        self.orig = orig
        self.f = f
    def write(self, s):
        try:
            self.orig.write(s)
        except Exception:
            pass
        try:
            self.f.write(s)
        except Exception:
            pass
    def flush(self):
        try:
            self.orig.flush()
        except Exception:
            pass
        try:
            self.f.flush()
        except Exception:
            pass

class R:
    def __init__(self, files, bits=2048):
        self.f = files
        self.bits = bits
        self.priv = None
        self.pub = None
    def gen_keys(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=self.bits)
        priv_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.f.write_priv(priv_pem)
        self.f.write_pub(pub_pem)
        self.priv = key
        self.pub = key.public_key()
    def load_keys(self):
        priv_b = self.f.load_priv()
        pub_b = self.f.load_pub()
        if priv_b:
            self.priv = serialization.load_pem_private_key(priv_b, password=None)
        if pub_b:
            self.pub = serialization.load_pem_public_key(pub_b)
    def ensure_keys(self):
        self.load_keys()
        if not self.priv or not self.pub:
            self.gen_keys()
    def encrypt(self, data):
        return self.pub.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    def decrypt(self, data):
        return self.priv.decrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

if __name__ == '__main__':
    files = Files()
    logf = files.open_log()
    old_out = sys.stdout
    old_err = sys.stderr
    sys.stdout = Tee(old_out, logf)
    sys.stderr = Tee(old_err, logf)
    try:
        print('--- RSA:')
        r = R(files)
        r.ensure_keys()
        print('ключи готовы:', files.priv_name, files.pub_name)
        plain = files.read_plain()
        print('прочитано байт открытого текста:', len(plain), 'из', files.in_name)
        try:
            cipher = r.encrypt(plain)
            files.write_cipher(cipher)
            files.write_cipher_b64(cipher)
            print('шифртекст записан в', files.cipher_name, 'и', files.cipher_b64_name,
                  'байт бинарного:', len(cipher))
        except Exception as e:
            print('ошибка при шифровании:', str(e))
            raise
        try:
            with open(files.cipher_name, 'rb') as f:
                cb = f.read()
            dec = r.decrypt(cb)
            files.write_dec(dec)
            print('дешифровано и записано в', files.dec_name, 'байт:', len(dec))
        except Exception as e:
            print('ошибка при дешифровании:', str(e))
            raise
        ok = dec == plain
        print('проверка совпадения исходного и расшифрованного:', ok)
        print('--- RSA: конец')
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        logf.close()
