# Name: Farrell Jeremy Hendrawan
# Student ID: 33497591

import sys


def z_algorithm(s):
    """
    Standard Z-algorithm. Computes the Z-array for string s in O(n) time.
    Z[i] = length of the longest substring starting at i that matches a prefix of s.
    Z[0] is set to len(s).
    """
    n = len(s)
    z = [0] * n
    z[0] = n 
    
    l, r = 0, 0  # current Z-box [l, r]
    
    for i in range(1, n):
        if i > r:
            # Case 1: i is outside any Z-box, compute from scratch
            l, r = i, i
            while r < n and s[r - l] == s[r]:
                r += 1
            z[i] = r - l
            r -= 1
        else:
            # Case 2: i is inside the current Z-box [l, r]
            k = i - l
            if z[k] < r - i + 1:
                # Case 2a: fully inside the box, just copy
                z[i] = z[k]
            else:
                # Case 2b: extends past the box, match from r+1 onwards
                l = i
                while r < n and s[r - l] == s[r]:
                    r += 1
                z[i] = r - l
                r -= 1
    
    return z


def calculate_z_suffix(s):
    """
    Calculates Z_suffix array for string s in O(n) time.
    Z_suffix[i] = length of longest substring ENDING at position i
                  that matches a SUFFIX of s.
    Done by reversing s, running Z, then reversing the result.
    """
    n = len(s)
    reversed_s = s[::-1]
    z_reversed = z_algorithm(reversed_s)
    
    z_suffix = [0] * n

    # Mirror z_reversed back so that position i in original string 
    # corresponds to position (n-1-i) in the reversed string
    for i in range(n):
        z_suffix[i] = z_reversed[n - 1 - i]
    z_suffix[n - 1] = n  # last position matches full suffix
    
    return z_suffix


def build_goodp(pat):
    """
    Build the goodp lookup table.
    
    goodp[kp1][x] = leftmost p (0-based) such that:
        1. pat[p..m-1] = pat[kp1..kp1 + (m-1-p)]
        2. pat[p-1] = x
    
    where kp1 = k+1, ranging from 0 to m.
    
    If no entry exists, default to p = m (shift past everything).
    """
    m = len(pat)
    z_suffix = calculate_z_suffix(pat)
    
    # One dict per kp1 value
    goodp = [dict() for _ in range(m + 1)]
    
    # Iterate p from RIGHT to LEFT so smaller p overwrites larger,
    # This leaves the p at the very left the valid p in the table.
    for p in range(m - 1, 0, -1):
        suffix_len = m - p          # length of suffix pat[p..m-1]
        x = pat[p - 1]              # character that must match the mismatch char
        
        # Find positions i in pat where Z_suffix[i] >= suffix_len.
        # This means pat[i-suffix_len+1 .. i] equals pat[p..m-1] (the suffix matches ending at i).
        # The starting index of the match is i - suffix_len + 1 = kp1
        # (the position on the right of where the mismatch would happen).
        for i in range(m - 1):  # exclude i = m-1 (full-suffix case)
            if z_suffix[i] >= suffix_len:
                kp1 = i - suffix_len + 1
                if 0 <= kp1 <= m:
                    goodp[kp1][x] = p
    
    return goodp


def find_matches(txt, pat):
    """
    Find all occurrences of pat in txt using the leftwards-shifting algorithm.
    Returns:
        matches: list of 0-based start positions where pat fully matches in txt
        runlog:  list of (j, k+1, p) tuples, one per iteration (all 0-based)
    """
    n = len(txt)
    m = len(pat)
    
    if m > n:
        return [], []
    
    goodp = build_goodp(pat)
    
    matches = []
    runlog = []
    
    j = n - m  # start with pat right-aligned
    
    # Main loop: right-align pat under txt, compare right-to-left, 
    # look up the shift in goodp, and slide pat leftwards
    while j >= 0:
        # Right-to-left scan from pat[m-1] down to pat[0]
        k = m - 1
        while k >= 0 and pat[k] == txt[j + k]:
            k -= 1
        
        # k = -1 means full match; otherwise k is the mismatch position
        if k < 0:
            matches.append(j)
        
        kp1 = k + 1  # 0 if full match, else position after mismatch
        
        # Mismatch character x: works for both cases since x = txt[j+k]
        # When k = -1 (full match): x = txt[j-1] (char to the left of the match)
        # When k >= 0 (mismatch):   x = txt[j+k] (the actual mismatch char)
        if j + k >= 0:
            x = txt[j + k]
        else:
            x = ''  # no character to the left, x can't match anything
        
        # Look up p in the goodp table; default to m if not found
        p = goodp[kp1].get(x, m)
        
        runlog.append((j, kp1, p))
        
        # Compute shift, with safety guard to make sure a shift always happens 
        shift = max(p - k - 1, 1)
        j -= shift
    
    return matches, runlog


def main():
    """Read text and pattern files, run matching, write output and runlog."""
    text_file = sys.argv[1]
    pattern_file = sys.argv[2]
    
    with open(text_file, 'r') as f:
        txt = f.read().strip()
    with open(pattern_file, 'r') as f:
        pat = f.read().strip()
    
    matches, runlog = find_matches(txt, pat)
    
    # Output file: 1-based match positions, one per line
    with open('output_a1q1.txt', 'w') as f:
        for pos in matches:
            f.write(str(pos + 1) + '\n')
    
    # Runlog file: 0-based j, k+1, p per iteration
    with open('runlog_a1q1.txt', 'w') as f:
        for j, kp1, p in runlog:
            f.write(f"{j} {kp1} {p}\n")


if __name__ == '__main__':
    main()