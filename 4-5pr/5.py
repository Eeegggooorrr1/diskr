import random

def minimal_r_for_k(k):
    r = 1
    while True:
        n = k + r
        if 2 ** r >= n + 1:
            return r
        r += 1

def is_power_of_two(x):
    return x and (x & (x - 1)) == 0

def build_H(r, n):
    H = [[0] * n for _ in range(r)]
    for col in range(n):
        num = col + 1
        for i in range(r):
            H[i][col] = (num >> i) & 1
    return H

def print_H_rows(H):
    print("Матрица H:")
    for i, row in enumerate(H):
        print(f"r{i+1:>2}: " + "".join(str(b) for b in row))


def insert_info_bits_positions(info_bits, r):
    k = len(info_bits)
    n = k + r
    code = [0] * n
    j = 0
    for pos in range(1, n+1):
        if is_power_of_two(pos):
            code[pos-1] = 0
        else:
            code[pos-1] = info_bits[j]
            j += 1
    return code

def calculate_parity_bits_via_H(code, H):
    r = len(H)
    n = len(code)
    for i in range(r):
        s = 0
        for j in range(n):
            parity_pos = 2 ** i
            if j == parity_pos - 1:
                continue
            if H[i][j]:
                s ^= code[j]
        if parity_pos - 1 < n:
            code[parity_pos - 1] = s
    return code

def encode_hamming_via_H(info_bits, r):
    code = insert_info_bits_positions(info_bits, r)
    H = build_H(r, len(code))
    code = calculate_parity_bits_via_H(code, H)
    return code, H

def build_G(k, r):
    n = k + r
    H = build_H(r, n)
    info_positions = [pos for pos in range(1, n+1) if not is_power_of_two(pos)]
    if len(info_positions) != k:
        raise ValueError("Количество информационных позиций не равно k")
    G = []
    for j, pos in enumerate(info_positions):
        row = [0] * n
        row[pos-1] = 1
        for i in range(r):
            parity_pos = 2 ** i
            row[parity_pos - 1] = H[i][pos-1]
        G.append(row)
    return G, info_positions
def print_G(G):
    print("\nПорождающая матрица G:")
    for i, row in enumerate(G):
        print(f"{i+1:>2}: " + "".join(str(b) for b in row))

def multiply_alpha_by_G(alpha, G):
    k = len(alpha)
    n = len(G[0])
    beta = [0] * n
    for j in range(k):
        if alpha[j] == 1:
            for col in range(n):
                beta[col] ^= G[j][col]
    return beta

def add_global_parity(code):
    parity = sum(code) % 2
    return code + [parity]

def remove_global_parity(code_with_global):
    return code_with_global[:-1], code_with_global[-1]

def syndrome_from_received(received_n_bits, H):
    r = len(H)
    n = len(received_n_bits)
    S = [0] * r
    for i in range(r):
        s = 0
        for j in range(n):
            if H[i][j]:
                s ^= received_n_bits[j]
        S[i] = s
    return S

def syndrome_to_position(S):
    pos = 0
    for i, b in enumerate(S):
        if b:
            pos += 2 ** i
    return pos

def correct_by_syndrome(received_n_bits, pos):
    if 1 <= pos <= len(received_n_bits):
        received_n_bits[pos-1] ^= 1
    return received_n_bits

def extract_info_bits_from_n(n_bits):
    return [str(n_bits[pos-1]) for pos in range(1, len(n_bits)+1) if not is_power_of_two(pos)]

def random_info_bits(k):
    return [random.randint(0,1) for _ in range(k)]

def print_bits(label, bits):
    print(f"{label}: {''.join(str(b) for b in bits)}")

def run_tests_and_show(orig_code_with_global, H, info_positions):
    n_with_global = len(orig_code_with_global)
    n = n_with_global - 1
    orig = orig_code_with_global[:]

    print("\nтесты")

    info_positions_local = [pos for pos in range(1, n+1) if not is_power_of_two(pos)]
    pos_a = random.choice(info_positions_local)
    t_a = orig[:]
    t_a[pos_a-1] ^= 1
    rec_n_a, _ = remove_global_parity(t_a)
    S_a = syndrome_from_received(rec_n_a, H)
    pos_syn_a = syndrome_to_position(S_a)
    parity_a = sum(t_a) % 2
    print("\n Ошибка в информационном бите")
    print_bits("Исходный код", orig)
    print_bits("Код с ошибкой", t_a)
    print(f"Синдром {S_a}, позиция = {pos_syn_a}")
    if parity_a == 1 and pos_syn_a != 0:
        rec_n_a = correct_by_syndrome(rec_n_a, pos_syn_a)
        corrected_a = add_global_parity(rec_n_a)
        print_bits("Исправленный код", corrected_a)
    else:
        print("двойная ошибка" if parity_a == 0 and pos_syn_a != 0 else "невозможно исправить/нет ошибки")

    parity_positions = [2**i for i in range(len(H)) if 2**i <= n]
    pos_b = random.choice(parity_positions)
    t_b = orig[:]
    t_b[pos_b-1] ^= 1
    rec_n_b, _ = remove_global_parity(t_b)
    S_b = syndrome_from_received(rec_n_b, H)
    pos_syn_b = syndrome_to_position(S_b)
    parity_b = sum(t_b) % 2
    print("\nОшибка в проверочном бите")
    print_bits("Исходный код", orig)
    print_bits("Код с ошибкой", t_b)
    print(f"Синдром {S_b}, позиция = {pos_syn_b}")
    if parity_b == 1 and pos_syn_b != 0:
        rec_n_b = correct_by_syndrome(rec_n_b, pos_syn_b)
        corrected_b = add_global_parity(rec_n_b)
        print_bits("Исправленный код", corrected_b)
    else:
        print("двойная ошибка" if parity_b == 0 and pos_syn_b != 0 else "невозможно исправить/нет ошибки")
    t_c = orig[:]
    t_c[-1] ^= 1
    rec_n_c, _ = remove_global_parity(t_c)
    S_c = syndrome_from_received(rec_n_c, H)
    pos_syn_c = syndrome_to_position(S_c)
    parity_c = sum(t_c) % 2
    print("\nОшибка в глобальном бите (последний)")
    print_bits("Исходный код", orig)
    print_bits("Код с ошибкой", t_c)
    print(f"Синдром = {S_c}, позиция = {pos_syn_c}, parity={parity_c}")
    if parity_c == 1 and pos_syn_c == 0:
        corrected_c = t_c[:]
        corrected_c[-1] ^= 1
        print_bits("Исправленный код", corrected_c)
    else:
        print("невозможно исправить/нет ошибки")

    a, b = random.sample(range(1, n_with_global+1), 2)
    t_d = orig[:]
    t_d[a-1] ^= 1
    t_d[b-1] ^= 1
    rec_n_d, _ = remove_global_parity(t_d)
    S_d = syndrome_from_received(rec_n_d, H)
    pos_syn_d = syndrome_to_position(S_d)
    parity_d = sum(t_d) % 2
    print("\nДве ошибки")
    print_bits("Исходный код", orig)
    print_bits("Код с ошибками", t_d)
    print(f"Синдром = {S_d}, позиция = {pos_syn_d}, parity={parity_d}")
    if parity_d == 0 and pos_syn_d != 0:
        print("двойная ошибка")
    else:
        print("двойная ошибка")

def main():
    try:
        k = int(input("Введите k: ").strip())
        if k <= 0:
            raise ValueError()
    except Exception:
        print("Неверный ввод k.")
        return

    r_input = input("Введите r: ").strip()
    if r_input == "":
        r = minimal_r_for_k(k)
        print(f"Выбран минимальный r = {r}")
    else:
        try:
            r = int(r_input)
            if r <= 0:
                raise ValueError()
            min_r = minimal_r_for_k(k)
            if r < min_r:
                print(f"Введён r={r} слишком мал для k={k}. Использую r={min_r}.")
                r = min_r
        except Exception:
            print("Неверный ввод r.")
            return

    n = k + r
    print(f"k={k}, r={r}, n={n} (без глобального бита)")
    info = random_info_bits(k)
    print_bits("Информационная α", info)

    beta_via_H, H = encode_hamming_via_H(info, r)
    G, info_positions = build_G(k, r)
    beta_via_G = multiply_alpha_by_G(info, G)


    print()
    print_H_rows(H)
    print_G(G)

    code_with_global = add_global_parity(beta_via_H)
    print_bits("\nКод β с глобальным битом четности", code_with_global)

    with open("encoded_code.txt", "w", encoding="utf-8") as f:
        f.write(''.join(str(b) for b in code_with_global))
    print("Сохранено в 'encoded_code.txt'")

    err = input(f"\nВведите номер бита (1..{len(code_with_global)}) для внесения ошибки").strip()
    received = code_with_global[:]
    if err != "":
        try:
            p = int(err)
            if not (1 <= p <= len(received)):
                raise ValueError()
            received[p-1] ^= 1
            print_bits("Код с внесённой ошибкой", received)
        except Exception:
            print("Неверный номер. Пропускаем внесение ошибки.")
    else:
        print("Пользовательская ошибка не внесена.")

    rec_n, global_bit = remove_global_parity(received)
    S = syndrome_from_received(rec_n, H)
    pos = syndrome_to_position(S)
    parity_check = sum(received) % 2

    print(f"Синдром {S}, позиция = {pos}")

    corrected = received[:]
    if parity_check == 1 and pos == 0:
        corrected[-1] ^= 1
        print_bits("Исправленный код", corrected)
    elif parity_check == 1 and pos != 0:
        rec_n = correct_by_syndrome(rec_n, pos)
        corrected = add_global_parity(rec_n)
        print_bits("Исправленный код", corrected)
    elif parity_check == 0 and pos != 0:
        print("двойная ошибка")
    else:
        print("Ошибок не найдено")

    rec_n_after, _ = remove_global_parity(corrected)
    extracted = ''.join(extract_info_bits_from_n(rec_n_after)) if corrected else ""
    orig = ''.join(str(b) for b in info)
    print(f"\nα (оригинал)     = {orig}")
    print(f"извлечено         = {extracted}")
    print(("СОВПАДАЮТ" if orig == extracted else "НЕ СОВПАДАЮТ"))

    run_tests_and_show(code_with_global, H, info_positions)

    with open("input.txt", "w", encoding="utf-8") as f:
        f.write(''.join(str(b) for b in received))

if __name__ == "__main__":
    main()
