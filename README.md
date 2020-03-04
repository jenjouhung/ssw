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
$python3 mytest.py data/test1.txt  data/test2.txt
```

Now, it is possible to compare data from sentence.tsv, please use -p 
```
$python3 mytest.py -p data/pair1.tsv
```


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

