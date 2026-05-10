# Name: Farrell Jeremy Hendrawan
# Student ID: 33497591


import sys


def build_suffix_array(s):
    """
    Build the suffix array of s by explicit sorting of all suffixes.
    Returns SA where SA[i] is the 0-based start index of the i-th sorted suffix.
    """
    n = len(s)
    suffixes = [(s[i:], i) for i in range(n)]
    suffixes.sort()
    return [idx for (_suf, idx) in suffixes]


def build_bwt(s, sa):
    """
    Build the BWT (last column L) from string s and its suffix array sa.
    L[i] = s[sa[i] - 1], the cyclic predecessor of the suffix at row i.
    Negative indexing handles sa[i] == 0 correctly (wraps to s[-1] = '$').
    """
    n = len(s)
    return ''.join(s[sa[i] - 1] for i in range(n))


def build_rank(L):
    """
    Build the Rank table: rank[c] = first 0-based row in F where character c appears.
    Equivalently, the count of characters in L (or F) strictly less than c.
    """
    counts = {}
    for ch in L:
        counts[ch] = counts.get(ch, 0) + 1
    rank = {}
    running = 0
    # Walk distinct chars in sorted order, accumulating counts to get block start positions
    for ch in sorted(counts.keys()):
        rank[ch] = running
        running += counts[ch]
    return rank


def build_nocc(L):
    """
    Build number of occurrences table:
      nocc[c][i] = number of occurrences of c in L[0..i] (inclusive of i).
    Stored sparsely as a dict-of-lists; only chars present in L get a list.
    """
    n = len(L)
    chars = set(L)
    nocc = {c: [0] * n for c in chars}
    nocc[L[0]][0] = 1
    # Each column carries the previous column forward, then bumps the current char
    for i in range(1, n):
        for c in chars:
            nocc[c][i] = nocc[c][i - 1]
        nocc[L[i]][i] += 1
    return nocc


def nocc_query(nocc, c, hi, inclusive):
    """
    Obtains the number of occurrences of c in L:
      inclusive=True  -> count in L[0..hi]   (matches lecture's L[1..ep] inclusive)
      inclusive=False -> count in L[0..hi)   (matches lecture's L[1..sp) exclusive)
    Returns 0 if c does not appear in L.
    """
    if c not in nocc:
        return 0
    if inclusive:
        return nocc[c][hi] if hi >= 0 else 0
    else:
        return nocc[c][hi - 1] if hi >= 1 else 0


def positions_from_range(sp, ep, sa):
    """Convert a (sp, ep) inclusive row range to 0-based starting positions in txt."""
    if sp is None or sp > ep:
        return []
    return [sa[i] for i in range(sp, ep + 1)]


def backward_step (c, sp, ep, rank, nocc):
    """
    One backward-search update step for a single character c.
    Returns the new (sp, ep), or (None, None) if c is absent or the range becomes empty.
    """
    if c not in rank:
        return None, None
    new_sp = rank[c] + nocc_query(nocc, c, sp, inclusive=False)
    new_ep = rank[c] + nocc_query(nocc, c, ep, inclusive=True) - 1
    if new_sp > new_ep:
        return None, None
    return new_sp, new_ep


def backward_run(chars_right_to_left, sp, ep, rank, nocc):
    """
    Run a sequence of backward-search steps over the given chars (already in
    right-to-left order). Returns final (sp, ep) or (None, None) on empty range.
    """
    for c in chars_right_to_left:
        sp, ep = backward_step(c, sp, ep, rank, nocc)
        if sp is None:
            return None, None
    return sp, ep


def bwt_search_exact(pat, L, rank, nocc):
    """
    Standard BWT backward search for an exact pattern. Returns (sp, ep) row range
    or (None, None) on no match.
    """
    n = len(L)
    return backward_run(reversed(pat), 0, n - 1, rank, nocc)


def bwt_search_substitution(pat, pos, alphabet, L, rank, nocc, sa):
    """
    Find positions where a length-m txt substring matches pat exactly except at
    position `pos`, which is replaced by any character != pat[pos] (so distance is
    strictly 1, not 0).

    Strategy: backward search split at pos into a root branching point.
      1. Exact-search the right portion pat[pos+1..m-1].
      2. At pos, branch over each c in alphabet with c != pat[pos].
      3. Continue each branch independently with the prefix pat[0..pos-1].
    """
    n = len(L)
    skip_char = pat[pos]

    # Step 1: exact search on the right portion
    sp, ep = backward_run(reversed(pat[pos + 1:]), 0, n - 1, rank, nocc)
    if sp is None:
        return []

    # Step 2: branch over alphabet, excluding the original char to keep distance == 1
    branches = []
    for c in alphabet:
        if c == skip_char:
            continue
        bsp, bep = backward_step (c, sp, ep, rank, nocc)
        if bsp is not None:
            branches.append((bsp, bep))

    # Step 3: for each surviving branch, finish the search with the prefix
    left_part = pat[:pos]
    positions = []
    for bsp, bep in branches:
        fsp, fep = backward_run(reversed(left_part), bsp, bep, rank, nocc)
        if fsp is not None:
            positions.extend(positions_from_range(fsp, fep, sa))
    return positions


def bwt_search_transposition(pat, pos, L, rank, nocc, sa):
    """
    Find positions where a length-m txt substring matches pat with pat[pos] and
    pat[pos+1] swapped. Skip when those two chars are equal (no-op swap that
    would falsely flag an exact match as distance 1).
    """
    if pat[pos] == pat[pos + 1]:
        return []
    swapped = pat[:pos] + pat[pos + 1] + pat[pos] + pat[pos + 2:]
    sp, ep = bwt_search_exact(swapped, L, rank, nocc)
    return positions_from_range(sp, ep, sa)


def bwt_search_deletion(pat, pos, L, rank, nocc, sa):
    """
    Find positions where a length-(m-1) txt substring equals pat with pat[pos] removed.
    """
    shortened = pat[:pos] + pat[pos + 1:]
    if len(shortened) == 0:
        return []
    sp, ep = bwt_search_exact(shortened, L, rank, nocc)
    return positions_from_range(sp, ep, sa)


def bwt_search_insertion(pat, slot, alphabet, L, rank, nocc, sa):
    """
    Find positions where a length-(m+1) txt substring equals pat with one extra
    character inserted at the given slot (slot in [0, m]).
    Root branching mechanism, but with no skip char (any character is a valid insertion).
    """
    n = len(L)

    # Step 1: exact search on the suffix of pat (chars to the right of the inserted slot)
    sp, ep = backward_run(reversed(pat[slot:]), 0, n - 1, rank, nocc)
    if sp is None:
        return []

    # Step 2: branch over the full alphabet at the inserted slot
    branches = []
    for c in alphabet:
        bsp, bep = backward_step (c, sp, ep, rank, nocc)
        if bsp is not None:
            branches.append((bsp, bep))

    # Step 3: continue each branch with the prefix pat[0..slot-1]
    left_part = pat[:slot]
    positions = []
    for bsp, bep in branches:
        fsp, fep = backward_run(reversed(left_part), bsp, bep, rank, nocc)
        if fsp is not None:
            positions.extend(positions_from_range(fsp, fep, sa))
    return positions


def find_matches(txt, pat):
    """
    Find all txt positions where a substring matches pat with match-distance <= 1.
    Returns sorted [(1-based_position, distance), ...] with exact (0) taking
    precedence over distance 1 at the same position.
    txt is expected to already include the terminal '$'.
    """
    n = len(txt)
    m = len(pat)

    # Preprocessing: SA, BWT, Rank, nOcc
    sa = build_suffix_array(txt)
    L = build_bwt(txt, sa)
    rank = build_rank(L)
    nocc = build_nocc(L)

    # Alphabet for root branching, excludes the terminal,
    # since '$' must not appear inside any reported match.
    alphabet = sorted(set(txt) - {'$'})

    # Track best (smallest) distance per starting position
    best = {}

    def record(pos, dist):
        # Keep only the smallest distance per position which would implement the spec's
        # exact takes precedence rule.
        if pos not in best or dist < best[pos]:
            best[pos] = dist

    # 1) Exact match (distance 0)
    sp, ep = bwt_search_exact(pat, L, rank, nocc)
    for p in positions_from_range(sp, ep, sa):
        record(p, 0)

    # 2) Substitution (distance 1) - one search per substituted position
    for pos in range(m):
        for p in bwt_search_substitution(pat, pos, alphabet, L, rank, nocc, sa):
            record(p, 1)

    # 3) Transposition (distance 1) - swap each adjacent pair, requires m >= 2
    for pos in range(m - 1):
        for p in bwt_search_transposition(pat, pos, L, rank, nocc, sa):
            record(p, 1)

    # 4) Insertion (distance 1) - one search per insertion slot, m+1 slots total
    for slot in range(m + 1):
        for p in bwt_search_insertion(pat, slot, alphabet, L, rank, nocc, sa):
            record(p, 1)

    # 5) Deletion (distance 1) - drop each pat position; skip when m == 1
    # (deletion of the only char leads to empty pattern which would match).
    if m >= 2:
        for pos in range(m):
            for p in bwt_search_deletion(pat, pos, L, rank, nocc, sa):
                record(p, 1)

    # Convert to 1-based positions and sort
    return sorted((pos + 1, dist) for pos, dist in best.items())


def main():
    """
    Entry point: python a1q2.py <text filename> <pattern filename>
    Reads txt and pat, appends '$' terminal, runs the search, writes results to
    output_a1q2.txt as '<1-based pos> <0|1>' per line, sorted by position.
    """
    if len(sys.argv) != 3:
        print("Usage: python a1q2.py <text filename> <pattern filename>")
        sys.exit(1)

    txt_path = sys.argv[1]
    pat_path = sys.argv[2]

    # Read inputs (no line breaks per spec; strip just in case)
    with open(txt_path, 'r') as f:
        txt = f.read().strip()
    with open(pat_path, 'r') as f:
        pat = f.read().strip()

    # Append the unique terminal as required by the spec
    results = find_matches(txt + '$', pat)

    with open('output_a1q2.txt', 'w') as f:
        for pos, dist in results:
            f.write(f"{pos} {dist}\n")


if __name__ == "__main__":
    main()