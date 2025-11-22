import sys
import os

class Files:
    def __init__(self):
        self.in_name = 'task10_in.txt'
        self.pr_name = 'primes.txt'
        self.op_name = 'ops.txt'
        self.log_name = 'log.txt'
    def read_input(self):
        s = open(self.in_name, 'r', encoding='utf-8').read().strip().split()
        k = 5000
        m = 1000000001
        n = 65537
        for token in s:
            if token.startswith('k='):
                try:
                    k = int(token.split('=',1)[1])
                except:
                    pass
            if token.startswith('m='):
                try:
                    m = int(token.split('=',1)[1])
                except:
                    pass
            if token.startswith('n='):
                try:
                    n = int(token.split('=',1)[1])
                except:
                    pass
        if m < 3:
            m = 3
        if m % 2 == 0:
            m += 1
        return k, m, n
    def write_primes(self, lst):
        with open(self.pr_name, 'w', encoding='utf-8') as f:
            for v in lst:
                f.write(str(v) + '\n')
    def write_ops(self, s):
        with open(self.op_name, 'w', encoding='utf-8') as f:
            f.write(s)
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

class Genpr:
    def __init__(self, k, m):
        self.k = k
        self.m = m
        self.n = m + 2 * k - 2
        self.A = [1] * k
    def gen(self):
        if self.m <= 2:
            for i in range(self.k):
                val = self.m + 2*(i+1) - 2
                if val == 2:
                    self.A[i] = 1
                elif val < 3:
                    self.A[i] = 0
        d = 3
        while d <= self.n // d:
            j = self._find_j(d)
            if j is None:
                pass
            else:
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
            for j in range(1, d + 1):
                val = self.m + 2 * j - 2
                if val >= 3 and (val % d) == 0:
                    return j
            j = d + 1
            while True:
                val = self.m + 2 * j - 2
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

class Ops:
    def add(self, a, b):
        return a + b
    def sub(self, a, b):
        return a - b
    def mul(self, a, b):
        return a * b
    def div(self, a, b):
        if b == 0:
            raise ZeroDivisionError
        return a // b
    def mod(self, a, b):
        if b == 0:
            raise ZeroDivisionError
        return a % b

if __name__ == '__main__':
    files = Files()
    logf = files.open_log()
    old_out = sys.stdout
    old_err = sys.stderr
    sys.stdout = Tee(old_out, logf)
    sys.stderr = Tee(old_err, logf)
    try:
        k, m, n = files.read_input()
        print('параметры k,m,n =', k, m, n)
        gp = Genpr(k, m)
        primes = gp.gen()
        if len(primes) < 2:
            print('мало простых в интервале, попробую увеличить k вдвое и повторить')
            k2 = max(2*k, k+1000)
            gp2 = Genpr(k2, m)
            primes = gp2.gen()
        if len(primes) == 0:
            print('простых не найдено, завершаю')
            files.write_primes([])
            files.write_ops('no primes found\n')
            sys.exit(0)
        p = primes[0]
        q = primes[1] if len(primes) > 1 else primes[0]
        files.write_primes(primes)
        print('наибольшие найденные простые:', p, q)
        ops = Ops()
        s = []
        try:
            s.append('a = ' + str(p))
            s.append('b = ' + str(q))
            s.append('a + b = ' + str(ops.add(p,q)))
            s.append('a - b = ' + str(ops.sub(p,q)))
            s.append('b - a = ' + str(ops.sub(q,p)))
            s.append('a * b = ' + str(ops.mul(p,q)))
            try:
                s.append('a // b = ' + str(ops.div(p,q)))
            except ZeroDivisionError:
                s.append('a // b = деление на ноль')
            try:
                s.append('a % b = ' + str(ops.mod(p,q)))
            except ZeroDivisionError:
                s.append('a % b = деление на ноль')
            M = ops.mul(p,q)
            e = E()
            powres = e.powmod(p, n, M)
            s.append('a^n mod (a*b) = ' + str(powres))
        except Exception as ex:
            s.append('ошибка: ' + str(ex))
        outtxt = '\n'.join(s) + '\n'
        files.write_ops(outtxt)
        print('операции записаны в', files.op_name)
        print('список простых записан в', files.pr_name)
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        logf.close()
