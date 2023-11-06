import re
from inspect import getmembers, getmodule
from itertools import chain
from types import FunctionType, ModuleType


def moduletree(module: ModuleType):
    tree = {"children": [], "members": [], "module": module.__name__}
    for name, member in getmembers(module):
        if member == module:
            continue
        if isinstance(member, ModuleType):
            if not member.__name__.startswith(module.__name__):
                continue
            tree["children"].append(moduletree(member))
        elif getmodule(member) != module:
            continue
        elif not isinstance(member, (FunctionType, type)):
            continue
        else:
            tree["members"].append(member.__name__)
    return tree


def branch_to_lines(tree, level=0):
    headername = tree["module"]
    if '.' in headername:
        headername = '.'.join(headername.split('.')[1:])
    lines = [f"{'#' * min(level + 1, 3)} {headername}\n"]
    lines += [f"::: {tree['module']}"]
    lines += [f"::: {tree['module']}.{m}" for m in tree["members"]]
    lines.append('\n')
    lines += chain(
        *[
            branch_to_lines(c, level + 1) for c in tree["children"]
        ]
    )
    lines.append("\n")
    return lines


def write_to_markdown(lines, outpath):
    with open(outpath, "w") as stream:
        stream.write(re.sub('\n\n+', '\n\n', "\n".join(lines)))
