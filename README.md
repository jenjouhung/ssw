[![Build Status](https://travis-ci.org/vishnubob/ssw.svg?branch=master)](https://travis-ci.org/vishnubob/ssw)
[![Coverage Status](https://coveralls.io/repos/vishnubob/ssw/badge.svg?branch=master&service=github)](https://coveralls.io/github/vishnubob/ssw?branch=master)

#SSW: A Python Wrapper for the SIMD Smith-Waterman 
#With Unicode Text Comparsion Function

## Notice

 This Repository is forked from vishnubob/ssw, a great implemenation of swith waterman with SSE SIMD Command. However due to the limation of internal structue, the original version is not able to handle to the needs of comparing more than 128 differenet symbols at once. That's why we ceate this repo.

## How to test my code

I am not yet test the install command, it should work, but I am not sure. If you want to test it, please clone this repo, and run:

```
$python3 setup.py build_ext --inplace 
```
For compiling the c object

For testing (example), please  run: 
```
$python3 unissw.py data/test1.txt  data/test2.txt
```

## Command Line parameters

-p: source data in pair format (ID1 \tab Text1 \tab ID2 \tab Text2 )

```
$python3 unissw.py -p data/pair2.tsv
```

-v: with varaint characters comparsion. It will read varaint character file from /data/varinats.txt. If two characters are varinats, it will get +2 (by default), rather than mismacth score (-3 by default)

```
$python3 unissw.py -pv data/pair1.tsv
```

-o: to save comapre result to an external file
```
python3 unissw.py -o a.txt -pv data/P185n1618_10000_IDText.tsv
```

-d: print debug message

```
python3 unissw.py -pvd data/P185n1618_10000_IDText.tsv
```

-c: change the path of configure file.
```
python3 unissw.py -c config.json -pvd data/P185n1618_10000_IDText.tsv
```
if you didn't specify by -c, the system will read config.json in package root by default.

## About Configre.json
I have move few impoartant setting out from my code. Now you can revise the configure file to set those parameters for your task. Now the possible settings are:
```
{
  "gap_open_penalty": -3, 
  "gap_extend_penalty": -2,
  "match_score": 3,
  "variant_match_score": 2,
  "mismacth_penalty": -3,
  "with_variant": "True"
  "variant_file": "data/variants.txt"
}
```
All of them are optional, and above value equals the defualt values in the unissw program.


## Overview

[SSW][ssw_repo] is a fast implementation of the Smith-Waterman algorithm, which
uses the Single-Instruction Multiple-Data (SIMD) instructions to parallelize
the algorithm at the CPU level.  This repository wraps the SSW library into an
easy to install, high-level python interface with no external library dependancies.

The SSW library is written by Mengyao Zhao and Wan-Ping Lee, and this python
interface is maintained by Giles Hall.

## Installation

To install the SSW python package, use pip:

```
$ pip install ssw
```

## Example Usage

```
import ssw
aligner = ssw.Aligner()
alignment = aligner.align(reference="ACGTGAGAATTATGGCGCTGTGATT", query="ACGTGAGAATTATGCGCTGTGATT")
print(alignment.alignment_report())
Score = 45, Matches = 24, Mismatches = 0, Insertions = 0, Deletions = 1

ref   1   ACGTGAGAATTATGGCGCTGTGATT
          ||||||||||||| |||||||||||
query 1   ACGTGAGAATTAT-GCGCTGTGATT
```

[ssw_repo]: https://github.com/mengyao/Complete-Striped-Smith-Waterman-Library

