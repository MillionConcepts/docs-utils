import re
from inspect import getmembers, getmodule
from itertools import chain
from types import FunctionType, ModuleType


def moduletree(module: ModuleType):
    tree = {"module": module.__name__, "members": [], "children": []}
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
    lines.append("    options:")
    lines.append(f"        heading_level: {min(level + 1, 3)+1}\n")
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


def write_api(module: ModuleType, outpath, level=0):
    tree = moduletree(module)
    lines = branch_to_lines(tree, level)
    write_to_markdown(lines, outpath)
