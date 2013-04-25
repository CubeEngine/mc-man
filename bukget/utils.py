# Copypaste from here: http://en.wikibooks.org/wiki/Algorithm_implementation/Strings/Levenshtein_distance#Python
def levenshtein(s1, s2):
    """ Get the levenshtein edit distance between two strings
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[
                             j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

# Copypaste end

def get_best_match(to_match, possible_matches):
    """ Get the best match to the string in the iterable.
    """
    lowest_distance = -1
    distances = {}
    for match in possible_matches:
        distance = levenshtein(to_match, match)
        if lowest_distance < 0 or distance < lowest_distance:
            lowest_distance = distance
        if lowest_distance == 0:
            break
    for match in distances:
        if distances[match] == lowest_distance:
            return match
    return None
