from collections import Counter
import math
import csv


class FileManager:
    def load_text(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_text(self, path, text):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

    def save_char_stats(self, path, counts: Counter, total):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Character', 'Frequency', 'Probability'])
            for ch, cnt in counts.most_common():
                w.writerow([ch, cnt, f"{cnt}/{total}"])

    def save_char_codes(self, path, codes, counts: Counter, total):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Character', 'Probability', 'Code'])
            for ch, code in codes.items():
                w.writerow([ch, f"{counts[ch]}/{total}", code])

    def save_pair_stats(self, path, counts: Counter, total):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Pair', 'Frequency', 'Probability'])
            for p, cnt in counts.most_common():
                w.writerow([p, cnt, f"{cnt}/{total}"])

    def save_pair_codes(self, path, codes, counts: Counter, total):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Pair', 'Probability', 'Code'])
            for p, code in codes.items():
                w.writerow([p, f"{counts[p]}/{total}", code])


class Fano:
    def __init__(self, source_path='text.txt', file_manager=None):
        self.source_path = source_path
        self.io = file_manager if file_manager is not None else FileManager()

    def build_codes(self, items, codes, prefix=""):
        n = len(items)
        if n == 1:
            codes[items[0][0]] = prefix
            return
        if n == 2:
            codes[items[0][0]] = prefix + '0'
            codes[items[1][0]] = prefix + '1'
            return
        total = sum(w for _, w in items)
        cur = 0.0
        split = 1
        best_diff = float('inf')

        for i in range(1, n):
            cur += items[i - 1][1]
            diff = abs(total - 2 * cur)
            if diff < best_diff:
                best_diff = diff
                split = i

        left = items[:split]
        right = items[split:]
        self.build_codes(left, codes, prefix + '0')
        self.build_codes(right, codes, prefix + '1')

    def bits_to_text(self, bits, decoding_map):
        out = []
        pos = 0
        L = len(bits)
        while pos < L:
            for l in range(1, L - pos + 1):
                seg = bits[pos:pos + l]
                if seg in decoding_map:
                    out.append(decoding_map[seg])
                    pos += l
                    break
        return ''.join(out)

    def run(self):
        text = self.io.load_text(self.source_path)
        n_chars = len(text)
        print(f"Количество символов в тексте: {n_chars}\n")

        char_freq = Counter(text)
        distinct_chars = len(char_freq)
        sorted_chars = char_freq.most_common()
        char_list = [c for c, _ in sorted_chars]
        freq_list = [f for _, f in sorted_chars]
        prob_list = [f / n_chars for f in freq_list]

        self.io.save_char_stats('char_stats.csv', char_freq, n_chars)
        print("Статистика символов записана в char_stats.csv")

        H1 = -sum(p * math.log2(p) for p in prob_list if p > 0)
        print(f"Энтропия = {H1} бит на символ")

        uniform_len = math.ceil(math.log2(distinct_chars)) if distinct_chars > 1 else 1
        print(f"Длина кода при равномерном кодировании: {uniform_len} бит")
        print(f"Избыточность при равномерном кодировании: {uniform_len - H1} бит на символ")
        print()

        char_probs = [(ch, p) for ch, p in zip(char_list, prob_list)]
        char_codes = {}
        self.build_codes(char_probs, char_codes)

        self.io.save_char_codes('char_codes.csv', char_codes, char_freq, n_chars)
        print("Коды символов записаны в char_codes.csv")

        encoded_chars = ''.join(char_codes[ch] for ch in text)
        print(f"Текст закодирован символами. Длина битовой последовательности: {len(encoded_chars)} бит")
        self.io.write_text('encoded_chars.txt', encoded_chars)
        print("Закодированный текст сохранен в encoded_chars.txt")
        print()

        code_to_char = {c: ch for ch, c in char_codes.items()}
        decoded = self.bits_to_text(encoded_chars, code_to_char)
        print("Декодирование символов завершено успешно.")
        self.io.write_text('decoded_chars.txt', decoded)
        print("Декодированный текст сохранен в decoded_chars.txt")
        if decoded == text:
            print("Декодированный текст идентичен исходному.")
        else:
            print("Ошибка: декодированный текст отличается от исходного!")

        avg_char_code_length = sum(prob_list[i] * len(char_codes[ch]) for i, ch in enumerate(char_list))
        char_eff = H1 / avg_char_code_length
        print(f"\nСредняя длина кода для символов: {avg_char_code_length}")
        print(f"Эффективность кодирования символов: {char_eff}")

        pairs = [text[i:i + 2] for i in range(len(text) - 1)]

        pair_freq = Counter(pairs)
        total_pairs = len(pairs)
        distinct_pairs = len(pair_freq)
        sorted_pairs = pair_freq.most_common()
        pair_list = [p for p, _ in sorted_pairs]
        pair_prob_list = [cnt / total_pairs for _, cnt in sorted_pairs]

        print(f"Общее количество пар: {total_pairs}, уникальных пар: {distinct_pairs}\n")

        self.io.save_pair_stats('pair_stats.csv', pair_freq, total_pairs)
        print("Статистика пар символов записана в pair_stats.csv")

        H_pair = -sum(p * math.log2(p) for p in pair_prob_list if p > 0)
        print(f"Энтропия на пару символов: {H_pair} бит на пару")
        print(f"Энтропия на символ: {H_pair / 2} бит на символ")

        uniform_pair_len = math.ceil(math.log2(distinct_pairs)) if distinct_pairs > 1 else 1
        print(f"Длина равномерного кода для пар: {uniform_pair_len} бит на пару")
        print()

        pair_probs = [(p, prob) for p, prob in zip(pair_list, pair_prob_list)]
        pair_codes = {}
        self.build_codes(pair_probs, pair_codes)

        self.io.save_pair_codes('pair_codes.csv', pair_codes, pair_freq, total_pairs)
        print("Коды пар символов записаны в pair_codes.csv")

        encoded_pairs = ""
        remaining = ""
        i = 0
        while i < len(text) - 1:
            cur_pair = text[i:i + 2]
            if cur_pair in pair_codes:
                encoded_pairs += pair_codes[cur_pair]
            else:
                raise ValueError(f"Пара {repr(cur_pair)} отсутствует в таблице кодов")
            i += 2
        if i < len(text):
            remaining = text[i:]

        print(f"Текст закодирован парами символов. Длина битовой последовательности: {len(encoded_pairs)} бит")
        self.io.write_text('encoded_pairs.txt', encoded_pairs)
        print("Закодированный текст сохранен в encoded_pairs.txt")
        print()

        code_to_pair = {c: p for p, c in pair_codes.items()}
        decoded_pairs = self.bits_to_text(encoded_pairs, code_to_pair)
        final_decoded = decoded_pairs + remaining
        print("Декодирование пар символов завершено успешно.")
        self.io.write_text('decoded_pairs.txt', final_decoded)
        print("Декодированный текст сохранен в decoded_pairs.txt")
        if final_decoded == text:
            print("Декодированный текст идентичен исходному.")
        else:
            print("декодированный текст отличается от исходного")


        avg_pair_code_length = sum((pair_freq[p] / total_pairs) * len(pair_codes[p]) for p in pair_list)
        avg_pair_per_char = avg_pair_code_length / 2
        print(f"\nСредняя длина кода для пар: {avg_pair_code_length} бит на пару")
        print(f"Средняя длина кода на символ: {avg_pair_per_char} бит на символ")
        pair_eff = H_pair / avg_pair_code_length
        print(f"Эффективность кодирования пар: {pair_eff}")

        print("однобуквенные / двухбуквенные сочетания")
        print("Энтропия на символ:", H1,'/', H_pair / 2)
        print("Средняя длина кода:", avg_char_code_length,'/', avg_pair_per_char)
        print("Эффективность:", char_eff,'/', pair_eff)
        print("Общая длина (бит):", len(encoded_chars),'/', len(encoded_pairs))

        compr_rate = len(encoded_chars) / len(encoded_pairs)
        print(f"\nКоэффициент сжатия: {compr_rate}")
        if compr_rate > 1:
            print("Кодирование парами символов улучшило сжатие.")
        else:
            print("Кодирование парами символов не улучшило сжатие.")


if __name__ == "__main__":
    codec = Fano()
    codec.run()
