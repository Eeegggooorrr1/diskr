import re
import math
from collections import Counter
from itertools import permutations, combinations, product

CHECK_FILE = "check.txt"
INPUT_FILE = "input.txt"
CIPHER_FILE = "cipher.txt"
RECOVERED_FILE = "recovered.txt"
PARTIAL_RECOVERED_FILE = "partial_recovered.txt"
OUTPUT_LOG = "output.txt"

ALPHABET = " " + "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
m = len(ALPHABET)

_log_lines = []

def log_print(*args, **kwargs):
    s = " ".join(str(a) for a in args)
    print(s, **kwargs)
    _log_lines.append(s)

def input_logged(prompt=""):
    print(prompt, end="")
    _log_lines.append(prompt)
    try:
        resp = input()
    except EOFError:
        resp = ""
    _log_lines.append(resp)
    return resp

def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def modinv(a, mod):
    g, x, _ = egcd(a, mod)
    if g != 1:
        return None
    return x % mod

def allowed_a_values(mod):
    return [a for a in range(1, mod) if math.gcd(a, mod) == 1]

def preprocess_and_save_corpus(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        raise
    raw = raw.lower()
    cleaned = re.sub(r"[^а-яё ]", " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    return cleaned

def analyze_input_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        raise
    raw_lower = raw.lower()
    cleaned = re.sub(r"[^а-яё ]", " ", raw_lower)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return raw, cleaned

def build_freq_table_from_corpus(text):
    cnt = Counter(ch for ch in text if ch in ALPHABET)
    total = sum(cnt.values())
    if total == 0:
        eps = 1.0 / (m * 1000.0)
        return {ch: eps for ch in ALPHABET}
    freq = {}
    eps = 1e-9
    for ch in ALPHABET:
        freq[ch] = cnt.get(ch, 0) / total
        if freq[ch] == 0:
            freq[ch] = eps
    s = sum(freq.values())
    for ch in freq:
        freq[ch] /= s
    return freq

def pretty_print_freq_table(freq, title):
    items = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    log_print("")
    log_print(title)
    log_print("символ | частота")
    for ch, p in items:
        display = "[space]" if ch == " " else ch
        log_print(f"{display!r:7} | {p:.6f}")
    log_print("")

def char_to_index(ch):
    try:
        return ALPHABET.index(ch)
    except ValueError:
        return None

def index_to_char(i):
    return ALPHABET[i % m]

def encrypt_char(ch, a, b):
    idx = char_to_index(ch)
    if idx is None:
        return ch
    return index_to_char((a * idx + b) % m)

def decrypt_char_with_a_inv(ch, a_inv, b):
    idx = char_to_index(ch)
    if idx is None:
        return ch
    return index_to_char((a_inv * (idx - b)) % m)

def encrypt_text(text, a, b):
    text = text.lower()
    return "".join(encrypt_char(ch, a, b) for ch in text)

def freq_counts(text):
    cnt = Counter()
    for ch in text:
        if ch in ALPHABET:
            cnt[ch] += 1
    return cnt

def chi_squared_score(text, expected_freq):
    cnt = freq_counts(text)
    total = sum(cnt.values())
    if total == 0:
        return float("inf")
    chi2 = 0.0
    for ch in ALPHABET:
        obs = cnt.get(ch, 0) / total
        exp = expected_freq.get(ch, 1e-9)
        chi2 += (obs - exp) ** 2 / exp
    return chi2

def attack_by_frequency_full(ciphertext, expected_freq, log_progress=True):
    allowed_as = allowed_a_values(m)
    total_keys = len(allowed_as) * m
    tested = 0
    best_score = float("inf")
    best_tuple = None
    results = []
    if log_progress:
        log_print("")
        log_print("полный перебор всех допустимых ключей (a,b)...")
    for a in allowed_as:
        a_inv = modinv(a, m)
        if a_inv is None:
            continue
        for b in range(m):
            tested += 1
            candidate = "".join(decrypt_char_with_a_inv(ch, a_inv, b) for ch in ciphertext.lower())
            score = chi_squared_score(candidate, expected_freq)
            results.append((score, a, b, candidate))
            if score < best_score:
                best_score = score
                best_tuple = (score, a, b)
                if log_progress:
                    log_print(f"Новый лучший: протестировано {tested}/{total_keys}, a={a}, b={b}, χ²={score:.6f}")
            if log_progress and tested % 50 == 0:
                log_print(f"протестировано {tested}/{total_keys} ключей, текущий лучший χ²={best_score:.6f} (a={best_tuple[1]}, b={best_tuple[2]})")
    results.sort(key=lambda x: x[0])
    if log_progress:
        log_print(f"Полный перебор закончен. Всего протестировано {tested} ключей. Лучший χ²={results[0][0]:.6f} при a={results[0][1]}, b={results[0][2]}")
    return results

def generate_candidates_by_frequency(expected_freq, ciphertext, top_k_check=5, top_k_cipher=5):
    check_sorted = sorted(expected_freq.items(), key=lambda x: x[1], reverse=True)
    top_check = [ch for ch, _ in check_sorted[:top_k_check]]
    cnt_cipher = Counter(ch for ch in ciphertext.lower() if ch in ALPHABET)
    cipher_sorted = [ch for ch, _ in cnt_cipher.most_common(top_k_cipher)]
    log_print("")
    log_print(f"Генерация кандидатов по частотному сопоставлению")
    log_print("Топ по корпусу:", top_check)
    log_print("Топ по шифротексту:", cipher_sorted)
    candidates = set()
    attempted_pairs = 0
    skipped_no_inv = 0
    for x1, x2 in permutations(top_check, 2):
        ix1 = char_to_index(x1)
        ix2 = char_to_index(x2)
        dx = (ix2 - ix1) % m
        if math.gcd(dx, m) != 1:
            continue
        for y1, y2 in permutations(cipher_sorted, 2):
            attempted_pairs += 1
            iy1 = char_to_index(y1)
            iy2 = char_to_index(y2)
            dy = (iy2 - iy1) % m
            inv_dx = modinv(dx, m)
            if inv_dx is None:
                skipped_no_inv += 1
                continue
            a = (dy * inv_dx) % m
            if math.gcd(a, m) != 1:
                skipped_no_inv += 1
                continue
            b = (iy1 - a * ix1) % m
            candidates.add((a, b))
    log_print(f"Попробовано пар: {attempted_pairs}. Сгенерировано ключей: {len(candidates)}. Пропущено пар из-за необратимости: {skipped_no_inv}.")
    return list(candidates)

def evaluate_candidates(candidates, ciphertext, expected_freq, log_progress=True):
    results = []
    total = len(candidates)
    if log_progress:
        log_print("")
        log_print(f"Оцениваю {total} сгенерированных кандидатов")
    for i, (a, b) in enumerate(candidates, start=1):
        a_inv = modinv(a, m)
        if a_inv is None:
            continue
        candidate_text = "".join(decrypt_char_with_a_inv(ch, a_inv, b) for ch in ciphertext.lower())
        score = chi_squared_score(candidate_text, expected_freq)
        results.append((score, a, b, candidate_text))
        if log_progress and i % 10 == 0:
            log_print(f"Оценено {i}/{total} кандидатов; текущ лучший χ² среди оценённых = {min(results)[0]:.6f}")
    results.sort(key=lambda x: x[0])
    if log_progress and results:
        log_print(f"Оценка кандидатов завершена. Лучший χ² из кандидатов = {results[0][0]:.6f} (a={results[0][1]}, b={results[0][2]})")
    return results

def interactive_pick_candidate(sorted_candidates):
    PREVIEW_LEN = 60
    step = 5
    total = len(sorted_candidates)
    idx = 0
    while idx < total:
        end = min(idx + step, total)
        log_print(f"\nКандидаты {idx+1}..{end} из {total}:")
        for i in range(idx, end):
            score, a, b, cand = sorted_candidates[i]
            preview = cand[:PREVIEW_LEN].replace("\n", " ")
            log_print(f"{i-idx+1}. χ²={score:.6f}, a={a}, b={b}, preview: {preview!r}")
        resp = input_logged("Есть ли среди показанных нужный вариант? (y - да, n - нет, q - выход): ").strip().lower()
        if resp == "q":
            log_print("Пользователь завершил выбор.")
            return None
        if resp == "y":
            sel_str = input_logged(f"Введите номер варианта (1..{end-idx}): ").strip()
            try:
                sel = int(sel_str)
            except ValueError:
                log_print("Неверный ввод номера; продолжаем.")
                idx += step
                continue
            if not (1 <= sel <= (end - idx)):
                log_print("Номер вне диапазона; продолжаем.")
                idx += step
                continue
            chosen = sorted_candidates[idx + sel - 1]
            log_print(f"Выбран вариант {idx + sel}: a={chosen[1]}, b={chosen[2]}, χ²={chosen[0]:.6f}")
            return chosen
        idx += step
        log_print("Показываю следующую пачку...")
    log_print("Кандидаты кончились.")
    return None

def _file_exists(path):
    try:
        with open(path, "r", encoding="utf-8"):
            return True
    except Exception:
        return False

def flush_log():
    try:
        with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(_log_lines))
    except Exception as e:
        print("Ошибка при записи лога:", e)

def partial_decrypt_by_freq_mapping(ciphertext, expected_freq):
    freq_cipher = build_freq_table_from_corpus(ciphertext)
    sorted_cipher = [ch for ch, _ in sorted(freq_cipher.items(), key=lambda x: x[1], reverse=True)]
    sorted_check = [ch for ch, _ in sorted(expected_freq.items(), key=lambda x: x[1], reverse=True)]
    mapping = {}
    for c_sym, check_sym in zip(sorted_cipher, sorted_check):
        mapping[c_sym] = check_sym
    out_chars = []
    for ch in ciphertext.lower():
        if ch in mapping:
            out_chars.append(mapping[ch])
        else:
            out_chars.append(ch)
    return "".join(out_chars)

def main():
    try:
        corpus = preprocess_and_save_corpus(CHECK_FILE)
    except FileNotFoundError:
        log_print(f"Ошибка: файл корпуса '{CHECK_FILE}' не найден.")
        flush_log()
        return
    if len(corpus) == 0:
        log_print(f"После очистки '{CHECK_FILE}' корпус пуст.")
        flush_log()
        return
    expected_freq = build_freq_table_from_corpus(corpus)
    pretty_print_freq_table(expected_freq, "Таблица частот по check.txt:")

    try:
        raw_input_text, cleaned_input = analyze_input_file(INPUT_FILE)
    except FileNotFoundError:
        log_print(f"Ошибка: входной файл '{INPUT_FILE}' не найден.")
        flush_log()
        return

    allowed = allowed_a_values(m)
    log_print("Допустимые значения a:", allowed)
    try:
        a_str = input_logged("Введите a (целое из списка): ").strip()
        b_str = input_logged(f"Введите b (целое 0..{m-1}): ").strip()
        a = int(a_str); b = int(b_str)
    except ValueError:
        log_print("Ошибка: a и b должны быть целыми. Завернение.")
        flush_log()
        return
    if a not in allowed or not (0 <= b < m):
        log_print("Ошибка: недопустимые a или b. Завершение.")
        flush_log()
        return

    cipher_text = encrypt_text(raw_input_text, a, b)
    with open(CIPHER_FILE, "w", encoding="utf-8") as f:
        f.write(cipher_text)
    log_print(f"Зашифрованный текст записан в '{CIPHER_FILE}' (a={a}, b={b}).")
    cnt_cipher = Counter(ch for ch in cipher_text.lower() if ch in ALPHABET)
    total_cipher = sum(cnt_cipher.values())
    log_print(f"Длина шифртекста (символы из алфавита): {total_cipher}")

    freq_cipher = build_freq_table_from_corpus(cipher_text)
    pretty_print_freq_table(freq_cipher, "Таблица частот по зашифрованному input.txt:")

    partial = partial_decrypt_by_freq_mapping(cipher_text, expected_freq)
    try:
        with open(PARTIAL_RECOVERED_FILE, "w", encoding="utf-8") as f:
            f.write(partial)
        preview = partial[:200].replace("\n", " ")
        log_print(f"Частично расшифрованный текст записан в '{PARTIAL_RECOVERED_FILE}'. Превью: {preview!r}")
    except Exception as e:
        log_print("Ошибка при сохранении:", e)
    top_k_check = 4
    top_k_cipher = 4
    candidates = generate_candidates_by_frequency(expected_freq, cipher_text, top_k_check, top_k_cipher)
    if candidates:
        evaluated = evaluate_candidates(candidates, cipher_text, expected_freq)
        chosen = interactive_pick_candidate(evaluated)
        if chosen is None:
            log_print("Ни один кандидат из shortlist не выбран. Переход к полному перебору.")
            full_results = attack_by_frequency_full(cipher_text, expected_freq)
            chosen = interactive_pick_candidate(full_results)
            if chosen is None:
                log_print("Не выбран ни один кандидат после полного перебора; recovered.txt не обновлён.")
            else:
                with open(RECOVERED_FILE, "w", encoding="utf-8") as f:
                    f.write(chosen[3])
                log_print(f"Выбранный вариант записан в '{RECOVERED_FILE}'.")
        else:
            with open(RECOVERED_FILE, "w", encoding="utf-8") as f:
                f.write(chosen[3])
            log_print(f"Выбранный вариант записан в '{RECOVERED_FILE}'.")
    else:
        log_print("частотное сопоставление не дало кандидатов. Запускаю полный перебор.")
        full_results = attack_by_frequency_full(cipher_text, expected_freq)
        chosen = interactive_pick_candidate(full_results)
        if chosen is None:
            log_print("Не выбран ни один кандидат после полного перебора; recovered.txt не обновлён.")
        else:
            with open(RECOVERED_FILE, "w", encoding="utf-8") as f:
                f.write(chosen[3])
            log_print(f"Выбранный вариант записан в '{RECOVERED_FILE}'.")
    flush_log()

if __name__ == "__main__":
    main()
