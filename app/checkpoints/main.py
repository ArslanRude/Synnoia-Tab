import re

_SENTENCE_END = re.compile(r'[.!?]\s*$')
_PARA_BREAK   = re.compile(r'\n{2,}')
_MULTI_SPACE  = re.compile(r'  +')

def apply_checkpoints(suggestion: str, prefix: str, suffix: str) -> str | None:
    """Apply all post-processing checkpoints to the suggestion.
    
    Returns the cleaned suggestion string, or None if it should be discarded.
    """
    # CP1 — Empty or whitespace-only output
    if not suggestion or not suggestion.strip():
        return None
    
    # CP2 — Exact duplicate of prefix tail
    if prefix.rstrip().endswith(suggestion.strip()):
        return None
    
    # CP3 — Space injection / removal at boundaries
    # Handle prefix leading space
    if prefix:
        if prefix[-1] not in ' \t\n\r([{"\'':
            # Prefix doesn't end with space - suggestion needs leading space
            if suggestion and suggestion[0] not in ' \t\n\r':
                suggestion = " " + suggestion
        else:
            # Prefix ends with space - strip leading space from suggestion to avoid double space
            if suggestion and suggestion[0] in ' \t\n\r':
                suggestion = suggestion.lstrip()
    
    # Handle suffix trailing space
    if suffix:
        if suffix[0] not in ' \t\n\r.,;:!?)]}\'"':
            # Suffix doesn't start with space/punct - suggestion needs trailing space
            if suggestion and suggestion[-1] not in ' \t\n\r':
                suggestion = suggestion + " "
        else:
            # Suffix starts with space/punct - strip trailing space from suggestion to avoid double space
            if suggestion and suggestion[-1] in ' \t\n\r':
                suggestion = suggestion.rstrip()
    
    # CP4 — Capitalise after sentence-ending punctuation
    if _SENTENCE_END.search(prefix.rstrip()):
        lstripped = suggestion.lstrip()
        leading = suggestion[:len(suggestion) - len(lstripped)]
        if lstripped:
            suggestion = leading + lstripped[0].upper() + lstripped[1:]
    
    # CP5 — Prefix-repetition strip
    prefix_words = prefix.split()
    for n in range(min(4, len(prefix_words)), 0, -1):
        tail = " ".join(prefix_words[-n:])
        stripped_sugg = suggestion.lstrip()
        if stripped_sugg.lower().startswith(tail.lower()):
            leading = suggestion[:len(suggestion) - len(stripped_sugg)]
            suggestion = leading + stripped_sugg[len(tail):]
            break
    
    # Re-run CP1 after CP5
    if not suggestion or not suggestion.strip():
        return None
    
    # CP6 — Suffix-overlap strip
    if suffix:
        suffix_head = suffix.lstrip()[:40]
        for length in range(min(len(suffix_head), len(suggestion)), 2, -1):
            if suggestion.rstrip().endswith(suffix_head[:length]):
                suggestion = suggestion.rstrip()[:-length]
                break
    
    # Re-run CP1 after CP6
    if not suggestion or not suggestion.strip():
        return None
    
    # CP7 — Multi-paragraph and newline guard
    para_match = _PARA_BREAK.search(suggestion)
    if para_match:
        suggestion = suggestion[:para_match.start()]
    
    if "\n" in suggestion:
        suggestion = suggestion[:suggestion.index("\n")]
    
    # Re-run CP1 after CP7
    if not suggestion or not suggestion.strip():
        return None
    
    # CP8 — Whitespace normalisation
    suggestion = _MULTI_SPACE.sub(' ', suggestion)
    suggestion = suggestion.rstrip()
    
    # Re-apply suffix boundary check after CP8 (it may have stripped needed trailing space)
    if suffix and suffix[0] not in ' \t\n\r.,;:!?)]}\'"':
        if suggestion and suggestion[-1] not in ' \t\n\r':
            suggestion = suggestion + " "
    
    # CP9 — Minimum meaningful length
    if len(suggestion.strip()) < 3:
        return None
    
    return suggestion
