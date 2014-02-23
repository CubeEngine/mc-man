""" Utilities. """


def levenshtein(x, y):
    """ Get the levenshtein edit distance between y strings. """
    if len(x) < len(y):
        return levenshtein(y, x)
    if len(y) == 0:
        return len(x)
    previous_row = range(len(y) + 1)
    for i, k in enumerate(x):
        current_row = [i + 1]
        for j, l in enumerate(y):
            insertions = previous_row[
                j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (k != l)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def remove_duplicates(plugins):
    """ Remove duplicate plugins from a list.

    This a list of Plugin objects as the argument.
    The Plugin objects only need to contain the slug.

    """
    new = list()
    for plugin in plugins:
        for qlugin in new:
            if plugin.slug == qlugin.slug:
                break
        else:
            new.append(plugin)
    return new
