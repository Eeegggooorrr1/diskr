import sys
import os
import base64

class Files:
    def __init__(self):
        self.in_name = 'plain.txt'
        self.enc_name = 'cipher.bin'
        self.b64_name = 'cipher.b64'
        self.dec_name = 'dec.txt'
        self.log_name = 'log.txt'
    def read_plain(self):
        with open(self.in_name, 'rb') as f:
            return f.read()
    def write_enc(self, b):
        with open(self.enc_name, 'wb') as f:
            f.write(b)
    def write_b64(self, b):
        with open(self.b64_name, 'w', encoding='utf-8') as f:
            f.write(b)
    def write_dec(self, b):
        with open(self.dec_name, 'wb') as f:
            f.write(b)
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

class Gamma:
    def __init__(self, seed, a=6364136223846793005, b=1442695040888963407, m=2**64):
        self.y = seed % m
        self.a = a
        self.b = b
        self.m = m
    def next64(self):
        self.y = (self.a * self.y + self.b) % self.m
        return self.y.to_bytes(8, 'little')

class Cipher:
    def __init__(self, files, seed):
        self.f = files
        self.seed = seed
        self.block = 8
    def xor(self, data, gamma):
        return bytes(x ^ y for x, y in zip(data, gamma))
    def run(self):
        print('--- гаммирование:')
        plain = self.f.read_plain()
        n_total = len(plain)
        print(f'прочитано байт: {n_total} из {self.f.in_name}')
        frag = plain
        print(f'будет зашифровано байт: {len(frag)}')
        g = Gamma(self.seed)
        enc_bytes = bytearray()
        i = 0
        while i < len(frag):
            gblock = g.next64()
            chunk = frag[i:i+self.block]
            enc_chunk = self.xor(chunk, gblock[:len(chunk)])
            enc_bytes.extend(enc_chunk)
            i += len(chunk)
        self.f.write_enc(bytes(enc_bytes))
        print(f'записан шифртекст: {self.f.enc_name} ({len(enc_bytes)} байт)')
        b64_text = base64.b64encode(bytes(enc_bytes)).decode('utf-8')
        self.f.write_b64(b64_text)
        print(f'записан шифртекст в base64: {self.f.b64_name}')
        g2 = Gamma(self.seed)
        dec_bytes = bytearray()
        i = 0
        while i < len(enc_bytes):
            gblock = g2.next64()
            chunk = enc_bytes[i:i+self.block]
            dec_chunk = self.xor(chunk, gblock[:len(chunk)])
            dec_bytes.extend(dec_chunk)
            i += len(chunk)
        self.f.write_dec(bytes(dec_bytes))
        print(f'дешифровано и записано: {self.f.dec_name} ({len(dec_bytes)} байт)')
        ok = bytes(dec_bytes) == frag
        print('проверка совпадения исходного и расшифрованного:', ok)
        print('--- гаммирование: конец')

if __name__ == '__main__':
    files = Files()
    logf = files.open_log()
    old_out = sys.stdout
    old_err = sys.stderr
    sys.stdout = Tee(old_out, logf)
    sys.stderr = Tee(old_err, logf)
    try:
        sin = input('введите целый сид для генератора (Enter = 1): ').strip()
        if sin:
            try:
                seed = int(sin)
            except Exception:
                seed = 1
        else:
            seed = 1
        c = Cipher(files, seed)
        c.run()
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        logf.close()