# Author: Hung-Shin Lee (hungshinlee@gmail.com)
# Apache 2.0

import csv
from pathlib import Path
from typing import Optional, Tuple

EXTRA_FORMOSAN_G2P = {
    "z": "z",
    "o": "o",
    "h": "h",
    "g": "g",
    "y": "j",
    "w": "w",
    "c": "ʦ",
    "u": "u",
    "f": "f",
    "v": "v",
    "j": "ɟ",
    "b": "b",
    "q": "q",
    "e": "e",
    "l": "l",
    "d": "d",
}


def lower_formosan_text(raw_text: str, language: str) -> str:
    text = list(raw_text.strip())
    if language == "賽夏":
        for i, char in enumerate(text):
            if char == "S":
                if i == 0:
                    text[i] = char.lower()
            else:
                text[i] = char.lower()
    elif language == "噶瑪蘭":
        for i, char in enumerate(text):
            if char == "R":
                text[i] = char
            else:
                text[i] = char.lower()
    else:
        for i, char in enumerate(text):
            text[i] = char.lower()

    text = "".join(text)

    return text


def load_g2p_from_csv(g2p_path: Path) -> dict:
    g2p = dict()
    with g2p_path.open(newline="", encoding="utf-8-sig") as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            language = row["Language"]
            dialect = row["Dialect"]
            if dialect == "-":
                lang_tag = f"{language}"
            else:
                lang_tag = f"{language}_{dialect}"

            for key in row:
                assert key
                if key in ["Language", "Dialect"]:
                    continue

                if row[key] == "-":
                    continue

                g2p[lang_tag] = g2p.get(lang_tag, {})
                g2p[lang_tag][key] = row[key].split(",")

            for g, p in EXTRA_FORMOSAN_G2P.items():
                if g not in g2p[lang_tag]:
                    g2p[lang_tag][g] = p

    for lang_tag in g2p:
        # 按照 key 的字元長度排序
        g2p[lang_tag] = dict(
            sorted(g2p[lang_tag].items(), key=lambda x: len(x[0]), reverse=True)
        )

    return g2p


def replace_to_list(text: str, g2p: dict) -> Tuple[list, set]:
    # 創建標記陣列，記錄哪些位置已被處理
    marked = [False] * len(text)

    # 創建結果列表和臨時緩衝區
    result = []
    buffer = ""
    oovs = set()

    # 處理文本
    i = 0
    while i < len(text):
        # 如果當前位置已經被處理過，跳過
        if marked[i]:
            i += 1
            continue

        # 尋找匹配的 key
        found_key = None
        found_pos = -1

        for key in g2p:
            # 檢查當前位置是否匹配 key
            if i + len(key) <= len(text) and text[i : i + len(key)] == key:
                # 檢查這個範圍是否已有部分被處理過
                if not any(marked[i : i + len(key)]):
                    found_key = key
                    found_pos = i
                    break

        # 如果找到匹配的 key
        if found_key:
            # 先保存緩衝區中的內容（如果有）
            if buffer:
                result.append(buffer)
                buffer = ""

            # 添加替換後的值到結果列表
            result.append(g2p[found_key][0])

            # 標記已處理的位置
            for j in range(found_pos, found_pos + len(found_key)):
                marked[j] = True

            # 移到下一個未處理的位置
            i = found_pos + len(found_key)
        else:
            # 沒有匹配的 key，添加到緩衝區
            buffer += text[i]
            oovs.add(text[i])
            i += 1

    # 不要忘記添加最後的緩衝區內容
    if buffer:
        result.append(buffer)

    return result, oovs


def convert_to_ipa(
    text: str, g2p: dict, end_punctuations: list
) -> Tuple[Optional[str], list]:
    result_list = []
    oovs_to_ipa = set()

    for word in text.split():
        ending_punct = ""
        if word and word[-1] in end_punctuations:
            ending_punct = word[-1]
            word = word[:-1]

        ipa_list, oovs = replace_to_list(word, g2p)
        if len(oovs):
            oovs_to_ipa.update(oovs)
            continue

        ipa_string = "-".join(ipa_list) + ending_punct
        result_list.append(ipa_string)

    if len(oovs_to_ipa) or len(result_list) == 0:
        return None, sorted(oovs_to_ipa)

    result = " ".join(result_list)

    return result, []


if __name__ == "__main__":
    pass
