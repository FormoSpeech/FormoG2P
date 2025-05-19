# Author: Hung-Shin Lee (hungshinlee@gmail.com)
# Apache 2.0

import json
from pathlib import Path

import hydra
from datasets import load_dataset
from omegaconf import OmegaConf


def remove_punctuations(text: str):
    return (
        text.replace(".", "")
        .replace(",", "")
        .replace(";", "")
        .replace("?", "")
        .replace("!", "")
    )


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(args):
    print(OmegaConf.to_yaml(args))

    # ------- ARGS & PATHS
    lexicon_name = args.lexicon_name
    source_datasets = args.source_datasets

    lexicon_root = Path(args.lexicon_root)
    vowels_path = Path(args.vowels_path)
    with vowels_path.open() as file:
        vowels = json.load(file)

    # ------- RUN
    word2ipa = {}
    phonemes = {}
    for source in source_datasets:
        datasets_dir = Path(source)
        if not datasets_dir.exists():
            continue

        for dataset_path in datasets_dir.glob("*.jsonl"):
            lang_group = dataset_path.stem

            dataset = load_dataset("json", data_files=str(dataset_path), split="train")

            for item in dataset:
                transcript = item["transcript"].split()  # type: ignore
                ipa = item["ipa"].split()  # type: ignore

                if len(transcript) != len(ipa):
                    raise Exception(item)

                word2ipa[lang_group] = word2ipa.get(lang_group, {})
                phonemes[lang_group] = phonemes.get(lang_group, set())

                for i, word in enumerate(transcript):
                    word = remove_punctuations(word)
                    word2ipa[lang_group][word] = word2ipa[lang_group].get(word, set())

                    ipa_word = remove_punctuations(ipa[i])

                    word2ipa[lang_group][word].add(ipa_word)
                    phonemes[lang_group] = phonemes[lang_group].union(
                        ipa_word.split("-")
                    )

    vowels_and_consonants = set()
    for lang_group in word2ipa:
        word_to_ipa = {}
        for word in sorted(word2ipa[lang_group]):
            word_to_ipa[word] = sorted(word2ipa[lang_group][word])

        word2ipa_path = lexicon_root / lexicon_name / "word2ipa" / f"{lang_group}.json"
        word2ipa_path.parent.mkdir(exist_ok=True, parents=True)
        with word2ipa_path.open("w") as file:
            json.dump(
                word_to_ipa,
                file,
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
            )

        phonemes_path = lexicon_root / lexicon_name / "phonemes" / f"{lang_group}.txt"
        phonemes_path.parent.mkdir(exist_ok=True, parents=True)
        with phonemes_path.open("w") as file:
            for phoneme in sorted(phonemes[lang_group]):
                ords = " ".join([str(ord(p)) for p in phoneme])
                file.write(f"{phoneme} {ords}\n")
                vowels_and_consonants.add(phoneme)

    consonants = vowels_and_consonants.difference(vowels)
    consonants = sorted(consonants)
    consonants_path = lexicon_root / lexicon_name / "consonants.json"
    consonants_path.parent.mkdir(exist_ok=True, parents=True)
    with consonants_path.open("w") as file:
        json.dump(consonants, file, ensure_ascii=False, indent=4, sort_keys=True)

    vowels = sorted(vowels)
    vowels_path = lexicon_root / lexicon_name / "vowels.json"
    vowels_path.parent.mkdir(exist_ok=True, parents=True)
    with vowels_path.open("w") as file:
        json.dump(vowels, file, ensure_ascii=False, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
