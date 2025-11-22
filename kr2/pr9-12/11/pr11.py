import sys
import os

class Files:
    def __init__(self):
        self.plain = 'plain.txt'
        self.inp = 'rsa_in.txt'
        self.pr = 'rsa_primes.txt'
        self.keys = 'rsa_keys.txt'
        self.cipher = 'cipher.txt'
        self.dec = 'dec.txt'
        self.log = 'log.txt'
    def read_plain(self):
        if not os.path.exists(self.plain):
            s = 'ПОЗНАЙ СЕБЯ'
            with open(self.plain, 'w', encoding='utf-8') as f:
                f.write(s)
        with open(self.plain, 'r', encoding='utf-8') as f:
            return f.read().strip()
    def read_params(self):

        s = open(self.inp, 'r', encoding='utf-8').read().strip().split()

        for t in s:
            if t.startswith('k='):
                try:
                    k = int(t.split('=',1)[1])
                except:
                    pass
            if t.startswith('m='):
                try:
                    m = int(t.split('=',1)[1])
                except:
                    pass
        if m < 3:
            m = 3
        if m % 2 == 0:
            m += 1
        return k, m
    def write_primes(self, p, q):
        with open(self.pr, 'w', encoding='utf-8') as f:
            f.write(str(p) + '\n' + str(q) + '\n')
    def write_keys(self, N, e, d):
        with open(self.keys, 'w', encoding='utf-8') as f:
            f.write('N=' + str(N) + '\n')
            f.write('e=' + str(e) + '\n')
            f.write('d=' + str(d) + '\n')
    def write_cipher(self, blocks):
        with open(self.cipher, 'w', encoding='utf-8') as f:
            f.write(' '.join(str(x) for x in blocks))
    def write_dec(self, s):
        with open(self.dec, 'w', encoding='utf-8') as f:
            f.write(s)
    def open_log(self):
        return open(self.log, 'a', encoding='utf-8')

class Tee:
    def __init__(self, orig, f):
        self.orig = orig
        self.f = f
    def write(self, s):
        try:
            self.orig.write(s)
        except:
            pass
        try:
            self.f.write(s)
        except:
            pass
    def flush(self):
        try:
            self.orig.flush()
        except:
            pass
        try:
            self.f.flush()
        except:
            pass

class Genpr:
    def __init__(self, k, m):
        self.k = k
        self.m = m
        self.n = m + 2 * k - 2
        self.A = [1] * k
    def gen(self):
        for i in range(self.k):
            val = self.m + 2*(i+1) - 2
            if val < 3:
                self.A[i] = 0
        d = 3
        while d <= self.n // d:
            j = self._find_j(d)
            if j is not None:
                idx = j
                while idx <= self.k:
                    self.A[idx-1] = 0
                    idx += d
            if d % 6 == 1:
                d += 4
            else:
                d += 2
        primes = []
        for i in range(self.k, 0, -1):
            if self.A[i-1] == 1:
                val = self.m + 2*i - 2
                if val >= 2:
                    primes.append(val)
        return primes
    def _find_j(self, d):
        if d % 2 == 0:
            for j in range(1, d+1):
                val = self.m + 2*j - 2
                if val >= 3 and (val % d) == 0:
                    return j
            j = d + 1
            while True:
                val = self.m + 2*j - 2
                if val >= 3 and (val % d) == 0:
                    return j
                j += d
        inv2 = (d + 1) // 2
        t = (-(self.m - 2)) % d
        j = (t * inv2) % d
        if j == 0:
            j = d
        while self.m + 2 * j - 2 < 3:
            j += d
        return j

class E:
    def powmod(self, a, k, m):
        a = a % m
        K = k
        B = 1 % m
        A = a
        while True:
            q = K // 2
            r = K - 2 * q
            K = q
            if r != 0:
                B = (A * B) % m
            if K == 0:
                return B
            A = (A * A) % m

def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        return None
    return x % m

class RSA:
    def __init__(self, k, m):
        self.k = k
        self.m = m
        self.p = None
        self.q = None
        self.N = None
        self.phi = None
        self.e = None
        self.d = None
    def gen_primes(self):
        gp = Genpr(self.k, self.m)
        lst = gp.gen()
        if len(lst) < 2:
            gp2 = Genpr(self.k*2, self.m)
            lst = gp2.gen()
        if not lst:
            raise Exception('no primes found')
        if len(lst) == 1:
            self.p = lst[0]
            self.q = lst[0]
        else:
            self.p = lst[0]
            self.q = lst[1]
        self.N = self.p * self.q
        self.phi = (self.p - 1) * (self.q - 1)
    def choose_e(self):
        cand = 3
        while cand < self.phi:
            if gcd(cand, self.phi) == 1 and is_prime_small(cand):
                self.e = cand
                return
            cand += 2
        raise Exception('нету e')
    def compute_d(self):
        inv = modinv(self.e, self.phi)
        if inv is None:
            raise Exception('нету инв')
        self.d = inv

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def is_prime_small(n):
    if n < 2:
        return False
    small = [2,3,5,7,11,13,17,19,23,29]
    for s in small:
        if n == s:
            return True
        if n % s == 0:
            return False
    r = int(n**0.5)
    i = 31
    while i <= r:
        if n % i == 0:
            return False
        i += 2
    return True

class Codec:
    def __init__(self):
        letters = ['А','Б','В','Г','Д','Е','Ж','З','И','Й','К','Л','М','Н','О','П','Р','С','Т','У','Ф','Х','Ц','Ч','Ш','Щ','Ъ','Ы','Ь','Э','Ю','Я']
        self.enc = {}
        for i, ch in enumerate(letters, start=1):
            self.enc[ch] = '{:02d}'.format(9 + i)
        self.enc[' '] = '99'
        self.dec = {v:k for k,v in self.enc.items()}
    def text_to_tokens(self, s):
        s = s.upper()
        toks = []
        for ch in s:
            if ch in self.enc:
                toks.append(self.enc[ch])
            else:
                toks.append('99')
        return toks
    def tokens_to_text(self, toks):
        res = []
        for t in toks:
            if t in self.dec:
                res.append(self.dec[t])
            else:
                res.append('?')
        return ''.join(res)

def split_blocks(tokens, N):
    blocks = []
    counts = []
    i = 0
    L = len(tokens)
    while i < L:
        curr = tokens[i]
        if int(curr) >= N:
            raise Exception('токен >= N')
        j = i + 1
        while j <= L:
            num = int(''.join(tokens[i:j]))
            if num < N:
                j += 1
                continue
            else:
                break
        j -= 1
        if j == i:
            blk = int(tokens[i])
            cnt = 1
            i += 1
        else:
            blk = int(''.join(tokens[i:j]))
            cnt = j - i
            i = j
        blocks.append(blk)
        counts.append(cnt)
    return blocks, counts

if __name__ == '__main__':
    f = Files()
    logf = f.open_log()
    old_out = sys.stdout
    old_err = sys.stderr
    sys.stdout = Tee(old_out, logf)
    sys.stderr = Tee(old_err, logf)
    try:
        k, m = f.read_params()
        print('параметры генерации k,m =', k, m)
        rsa = RSA(k, m)
        rsa.gen_primes()
        rsa.choose_e()
        rsa.compute_d()
        f.write_primes(rsa.p, rsa.q)
        f.write_keys(rsa.N, rsa.e, rsa.d)
        print('p,q =', rsa.p, rsa.q)
        print('N =', rsa.N)
        print('phi =', rsa.phi)
        print('e =', rsa.e)
        print('d =', rsa.d)
        codec = Codec()
        text = f.read_plain()
        print('исходный текст:', text)
        toks = codec.text_to_tokens(text)
        print('токенов всего:', len(toks))
        blocks, counts = split_blocks(toks, rsa.N)
        print('блоков для шифрования:', len(blocks))
        f.write_cipher([0])
        eproc = E()
        cipher_blocks = []
        for b in blocks:
            c = eproc.powmod(b, rsa.e, rsa.N)
            cipher_blocks.append(c)
        f.write_cipher(cipher_blocks)
        print('зашифровано, записано в', f.cipher)
        dec_blocks = []
        for c in cipher_blocks:
            mblk = eproc.powmod(c, rsa.d, rsa.N)
            dec_blocks.append(mblk)
        rebuilt = []
        for val, cnt in zip(dec_blocks, counts):
            width = cnt * 2
            s = str(val).zfill(width)
            token_list = [s[i:i+2] for i in range(0, len(s), 2)]
            rebuilt.extend(token_list)
        plain_rec = codec.tokens_to_text(rebuilt)
        f.write_dec(plain_rec)
        print('восстановленный текст:', plain_rec)
        print('файлы:', f.pr, f.keys, f.cipher, f.dec, f.log)
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        logf.close()
