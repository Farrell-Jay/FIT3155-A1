import subprocess
import os

# Each test case: (test_name, txt, pat, expected_output)
test_cases = [
    ("Spec example",      "babbaababaababaababab", "aababaabab",  ["10", "5"]),
    ("No matches",        "abcdefghij",            "xyz",         []),
    ("Pattern > text",    "ab",                    "abcdef",      []),
    ("Single char",       "abcabc",                "a",           ["4", "1"]),
    ("Pattern = text",    "hello",                 "hello",       ["1"]),
    ("Overlapping",       "aaaaa",                 "aa",          ["4", "3", "2", "1"]),
]

passed = 0
failed = 0

for name, txt, pat, expected in test_cases:
    # Write the test input files
    with open('text.txt', 'w') as f:
        f.write(txt)
    with open('pattern.txt', 'w') as f:
        f.write(pat)
    
    # Run a1q1.py
    subprocess.run(['python', 'a1q1.py', 'text.txt', 'pattern.txt'], check=True)
    
    # Read output
    with open('output_a1q1.txt', 'r') as f:
        actual = [line.strip() for line in f.readlines() if line.strip()]
    
    # Compare (order matters since output is in iteration order, not sorted)
    if actual == expected:
        print(f"✓ PASS: {name}")
        passed += 1
    else:
        print(f"✗ FAIL: {name}")
        print(f"   txt = {txt!r}")
        print(f"   pat = {pat!r}")
        print(f"   expected: {expected}")
        print(f"   got:      {actual}")
        failed += 1

print(f"\n{passed}/{passed + failed} tests passed")