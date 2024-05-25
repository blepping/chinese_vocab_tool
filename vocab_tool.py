import argparse
import string
from collections import OrderedDict

import chinese_english_lookup as cel
from ckip_transformers import nlp


class Config:
    model = "bert-base"
    device = 0
    allow_no_definition = False
    hsk2_exclude = ()
    hsk3_exclude = ()
    hsk2_min = 5
    hsk2_max = 99
    hsk3_min = 3
    hsk3_max = 999
    hsk2_min_char = 0
    hsk3_min_char = 0
    length_min = 2
    length_max = 5
    count_min = 1
    count_max = 999999
    try_alternatives = 4
    skip_sequences = ()

    def __init__(self, args):
        for k in (
            "model",
            "device",
            "hsk2_min",
            "hsk2_max",
            "hsk3_min",
            "hsk3_max",
            "hsk2_min_char",
            "hsk3_min_char",
            "length_min",
            "length_max",
            "count_min",
            "count_max",
            "try_alternatives",
        ):
            setattr(self, k, getattr(args, k))
        if args.hsk2_exclude:
            self.hsk2_exclude = set(args.hsk2_exclude)
        if args.hsk3_exclude:
            self.hsk3_exclude = set(args.hsk3_exclude)
        self.skip_sequences = set() if not args.skip else set(args.skip)
        if args.skip_file:
            for fn in args.skip_file:
                with open(fn, "r") as fp:
                    lines = (line for line in (l_.strip() for l_ in fp) if line)
                    self.skip_sequences |= set(lines)
        print(args)


CONFIG = None

PUNCT_CHARS = string.punctuation + "。：？！，……‘`“”"


class HSK3(cel.HSK3):
    def get_level_for_word(self, word):
        idx = self.word_to_category_map.get(word.strip())
        return idx + 1 if idx is not None else None


HSK3 = HSK3()
HSK2 = cel.HSK2()
CELDICT = cel.Dictionary()


def find_subseq(needle, haystack):
    nlen, hlen = len(needle), len(haystack)
    result = []
    for idx in range(hlen):
        plen = 0
        for subidx in range(idx, hlen):
            chunk = haystack[subidx]
            clen = len(chunk)
            if needle[plen : plen + clen] != chunk:
                break
            plen += clen
            if plen == nlen:
                result.append((idx, (subidx - idx) + 1))
                break
    return result


def is_all_punct(s):
    return all(c in PUNCT_CHARS for c in s)


def filter_skips(segs):
    while True:
        found = 0
        for skipseq in CONFIG.skip_sequences:
            skips = find_subseq(skipseq, segs)
            if not skips:
                continue
            found += 1
            offs = 0
            for skidx_, sslen in skips:
                skidx = skidx_ - offs
                segs = (*segs[:skidx], *segs[skidx + sslen :])
                offs += sslen
        if found == 0:
            break
    return segs


def get_segs(text):
    driver = nlp.CkipWordSegmenter(model=CONFIG.model, device=CONFIG.device)
    result = []
    segmented = driver((text,), use_delim=True)
    for chunk in segmented:
        if not chunk:
            continue
        filtered = tuple(
            w
            for w in (w.strip() for w in chunk)
            if w and not is_all_punct(w) and not w.isascii()
        )
        filtered = filter_skips(filtered)
        if not filtered:
            continue
        result.append(filtered)
    return result


def build_counts(segslist):
    result = OrderedDict()
    len_min, try_alts = CONFIG.length_min, CONFIG.try_alternatives
    skip_seqs = CONFIG.skip_sequences
    flattened = tuple(w for ws in segslist for w in ws)
    for idx in range(len(flattened)):
        chunk = "".join(flattened[idx : idx + try_alts])
        alts = {flattened[idx]}
        for altlen in range(CONFIG.length_min, min(len(chunk), CONFIG.length_max)):
            curralt = chunk[:altlen]
            if len(curralt) < len_min or curralt in skip_seqs:
                continue
            alts.add(curralt)
            for widx, w in enumerate(alts):
                if len(w) < len_min:
                    continue
                entry = result.get(w)
                if entry is None:
                    entry = (
                        1,
                        (
                            HSK2.get_level_for_word(w) or 0,
                            HSK3.get_level_for_word(w) or 0,
                            CELDICT.lookup(w),
                        ),
                    )
                    if widx == 0 and entry[1] == (None, None, None):
                        continue
                else:
                    entry = (entry[0] + 1, entry[1])
                result[w] = entry
    return result


CHAR_CACHE = {}


def check_characters(w):
    if CONFIG.hsk2_min_char < 1 and CONFIG.hsk3_min_char < 1:
        return True
    h2_ok, h3_ok = False, False
    for c in w:
        entry = CHAR_CACHE.get(w)
        if entry is None:
            entry = (HSK2.get_level_for_word(c) or 0, HSK3.get_level_for_word(c) or 0)
            CHAR_CACHE[w] = entry
        h2_ok = h2_ok or entry[0] == 0 or entry[0] >= CONFIG.hsk2_min_char
        h3_ok = h3_ok or entry[1] == 0 or entry[1] >= CONFIG.hsk3_min_char
        if h2_ok and h3_ok:
            return True
    return False


def filter_counts(counts):
    h2_min, h2_max = CONFIG.hsk2_min, CONFIG.hsk2_max
    h3_min, h3_max = CONFIG.hsk3_min, CONFIG.hsk3_max
    h2_exclude, h3_exclude = CONFIG.hsk2_exclude, CONFIG.hsk3_exclude
    len_min, len_max = CONFIG.length_min, CONFIG.length_max
    result = []
    for w, (count, (h2, h3, definition)) in tuple(counts.items()):
        if (
            (definition is None and not CONFIG.allow_no_definition)
            or (h2 in h2_exclude or h3 in h3_exclude)
            or (h2 > 0 and (h2 < h2_min or h2 > h2_max))
            or (h3 > 0 and (h3 < h3_min or h3 > h3_max))
            or (len(w) < len_min or len(w) > len_max)
            or (count < CONFIG.count_min or count > CONFIG.count_max)
            or not check_characters(w)
        ):
            continue
        result.append((w, count, h2, h3, definition))
    result.sort(key=lambda e: (e[1], e[3], e[2]), reverse=True)
    return result


def pad(s, pad_to):
    return s + (" " * (pad_to - len(s) * 2))


def go(fn):
    text = open(fn, "r").read().strip()
    segs = get_segs(text)
    counts = build_counts(segs)
    fcounts = filter_counts(counts)
    pad_to = CONFIG.length_max * 2
    for w, count, h2l, h3l, definition in fcounts:
        wpadded = pad(w, pad_to)
        def2 = str(definition).replace("\n", " | ")
        print(f"{count:>4}: {wpadded} -- {h2l:>2}, {h3l:>2}, {def2}")


def main():
    global CONFIG
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Chinese Vocab Tool",
    )
    parser.add_argument("input", type=str, help="Input file")
    parser.add_argument(
        "--model", type=str, default="bert-base", help="Segmenter model name"
    )
    parser.add_argument(
        "--device", type=int, default=0, help="Inference device (use -1 for CPU)"
    )
    parser.add_argument(
        "--hsk2-exclude",
        type=int,
        action="append",
        help="Exclude HSK 2 levels (may be specified multiple times)",
    )
    parser.add_argument(
        "--hsk3-exclude",
        type=int,
        action="append",
        help="Exclude HSK 3 levels (may be specified multiple times)",
    )
    parser.add_argument("--hsk2-min", type=int, default=1, help="Minimum HSK 2 level")
    parser.add_argument("--hsk2-max", type=int, default=9, help="Maximum HSK 2 level")
    parser.add_argument("--hsk3-min", type=int, default=1, help="Minimum HSK 3 level")
    parser.add_argument("--hsk3-max", type=int, default=9, help="Maximum HSK 3 level")
    parser.add_argument(
        "--hsk2-min-char",
        type=int,
        default=0,
        help="Requires at least one character in a word to be greater or equal to the minimum level (0 disables)",
    )
    parser.add_argument(
        "--hsk3-min-char",
        type=int,
        default=0,
        help="Requires at least one character in a word to be greater or equal to the minimum level (0 disables)",
    )
    parser.add_argument(
        "--allow-no-definition",
        action="store_true",
        help="Include entries with no CEDICT definition",
    )
    parser.add_argument("--length-min", type=int, default=2, help="Minimum word length")
    parser.add_argument("--length-max", type=int, default=5, help="Maximum word length")
    parser.add_argument("--count-min", type=int, default=1, help="Minimum occurences")
    parser.add_argument(
        "--count-max", type=int, default=9999999, help="Maximum occurences"
    )
    parser.add_argument(
        "--skip",
        type=str,
        action="append",
        help="Skip a word (may be specified multiple times)",
    )
    parser.add_argument(
        "--skip-file",
        type=str,
        action="append",
        help="Skip all words in a file (may be specified multiple times, file format should be one word per line)",
    )
    parser.add_argument(
        "--try-alternatives",
        type=int,
        default=5,
        help="Also try to look up prefixes of the segmented words up to length-max, will combine segments up to the specified length",
    )
    args = parser.parse_args()
    CONFIG = Config(args)
    go(args.input)


if __name__ == "__main__":
    main()
