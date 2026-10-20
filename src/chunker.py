MAX_TOKENS = 6000

def split_patch(patch, max_tokens=MAX_TOKENS):
    if len(patch) // 4 <= max_tokens:      # environ 4 caractères par token
        return [patch]
    hunks = patch.split("\n@@")
    parts, current = [], hunks[0]
    for h in hunks[1:]:
        h = "@@" + h
        if len(current + "\n" + h) // 4 > max_tokens:
            parts.append(current)
            current = h
        else:
            current += "\n" + h
    parts.append(current)
    return parts