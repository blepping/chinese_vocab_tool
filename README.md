# Chinese Vocab Tool
Commandline tool that uses AI word segmentation to generate Chinese vocab lists. Can filter by HSK level, word length and presence in CEDICT as well as customized exclude lists

## Features

- AI-based word segmentation
- Allows filtering words based on HSK 2, HSK 3 level or presence in dictionary
- Exclude lists
- Allows filtering words based on HSK (2 or 3) level of the component characters. For example, you could filter out words that don't have at least one HSK 3 at level 2 or higher.

## Setup

You'll need to have Python installed and know a little Python stuff here.

Create and activate a Python environment. On Unix-type OSes this would look like:

```sh
python -m venv venv
source venv/bin/activate
```

Install the requirements:

```sh
python -m pip install -r requirements.txt
```

## Usage

```plaintext
usage: vocab_tool.py [-h] [--model MODEL] [--device DEVICE] [--hsk2-exclude HSK2_EXCLUDE] [--hsk3-exclude HSK3_EXCLUDE] [--hsk2-min HSK2_MIN] [--hsk2-max HSK2_MAX] [--hsk3-min HSK3_MIN]
                     [--hsk3-max HSK3_MAX] [--hsk2-min-char HSK2_MIN_CHAR] [--hsk3-min-char HSK3_MIN_CHAR] [--allow-no-definition] [--length-min LENGTH_MIN] [--length-max LENGTH_MAX]
                     [--count-min COUNT_MIN] [--count-max COUNT_MAX] [--skip SKIP] [--skip-file SKIP_FILE] [--try-alternatives TRY_ALTERNATIVES]
                     input

Chinese Vocab Tool

positional arguments:
  input                 Input file

options:
  -h, --help            show this help message and exit
  --model MODEL         Segmenter model name (default: bert-base)
  --device DEVICE       Inference device (use -1 for CPU) (default: 0)
  --hsk2-exclude HSK2_EXCLUDE
                        Exclude HSK 2 levels (may be specified multiple times) (default: None)
  --hsk3-exclude HSK3_EXCLUDE
                        Exclude HSK 3 levels (may be specified multiple times) (default: None)
  --hsk2-min HSK2_MIN   Minimum HSK 2 level (default: 1)
  --hsk2-max HSK2_MAX   Maximum HSK 2 level (default: 9)
  --hsk3-min HSK3_MIN   Minimum HSK 3 level (default: 1)
  --hsk3-max HSK3_MAX   Maximum HSK 3 level (default: 9)
  --hsk2-min-char HSK2_MIN_CHAR
                        Requires at least one character in a word to be greater or equal to the minimum level (0 disables) (default: 0)
  --hsk3-min-char HSK3_MIN_CHAR
                        Requires at least one character in a word to be greater or equal to the minimum level (0 disables) (default: 0)
  --allow-no-definition
                        Include entries with no CEDICT definition (default: False)
  --length-min LENGTH_MIN
                        Minimum word length (default: 2)
  --length-max LENGTH_MAX
                        Maximum word length (default: 5)
  --count-min COUNT_MIN
                        Minimum occurences (default: 1)
  --count-max COUNT_MAX
                        Maximum occurences (default: 9999999)
  --skip SKIP           Skip a word (may be specified multiple times) (default: None)
  --skip-file SKIP_FILE
                        Skip all words in a file (may be specified multiple times, file format should be one word per line) (default: None)
  --try-alternatives TRY_ALTERNATIVES
                        Also try to look up prefixes of the segmented words up to length-max, will combine segments up to the specified length (default: 5)
```

You can use `--hsk2-exclude` and `--hsk3-exclude` to exclude only a specific level. No entry is considered level `0`.

Output will look like:

```plaintext
  12: 怪物       --  0,  3, 怪物 | 怪物 | 【guai4 wu5】 monster; freak; eccentric person
  12: 青铜       --  0,  0, 青铜 | 青銅 | 【qing1 tong2】 bronze (alloy of copper 銅|铜 and tin 錫|锡[xi1])
   9: 垫子       --  0,  4, 垫子 | 墊子 | 【dian4 zi5】 cushion; mat; pad
   9: 惨叫       --  0,  0, 惨叫 | 慘叫 | 【can3 jiao4】 to scream; blood-curdling screech; miserable shriek
   9: 呜呜       --  0,  0, 呜呜 | 嗚嗚 | 【wu1 wu1】 (interj) boo hoo
   9: 井口       --  0,  0, 井口 | 井口 | 【jing3 kou3】 entrance to mine
   6: 示意       --  6,  3, 示意 | 示意 | 【shi4 yi4】 to hint; to indicate (an idea to sb)
   6: 呼唤       --  6,  3, 呼唤 | 呼喚 | 【hu1 huan4】 to call out (a name etc); to shout
   6: 心思       --  0,  3, 心思 | 心思 | 【xin1 si5】 mind; thoughts; inclination; mood
   6: 木匠       --  0,  3, 木匠 | 木匠 | 【mu4 jiang4】 carpenter
```

Count, word -- HSK 2 level, HSK 3 level, definition

TBD: More useful output formats.
