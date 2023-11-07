"""
# example of use:
```
mt = moduletree('pdr', gitignore=True)
ml = modules_to_lines(mt)
write_to_markdown(ml, 'markdown_skeleton.md')
```
"""

from importlib import import_module
from inspect import getmembers
from itertools import chain
import os
from pathlib import Path
import re
from types import FunctionType, ModuleType

from hostess.directory import index_breadth_first, make_treeframe
from hostess.subutils import Viewer
from hostess.utilities import get_module
import pandas as pd


def get_valid_members(module):
    members = []
    for name, member in getmembers(module):
        if member == module:
            continue
        if isinstance(member, ModuleType):
            continue
        if not isinstance(member, (FunctionType, type)):
            continue
        else:
            members.append(member.__name__)
    return members


def _get_branch(name, level, tf):
    children, modules = tf.copy(), {}
    if level + 1 in tf.columns:
        children = children.loc[children[level + 1].isna()]
    if level != -1:
        children = children.loc[children[level] == name.split(".")[-1]]
    for c in children['filename']:
        if c == "__init__.py":
            mname = name
        else:
            mname = f"{name}.{c}".replace(".py", "")
        modules[mname] = {
            'name': mname, 'members': get_valid_members(import_module(mname))
        }
    return modules


def moduletree(root_module, gitignore=False):
    root = Path(get_module(root_module).__path__[0]).absolute()
    os.chdir(root)
    index = pd.DataFrame(index_breadth_first("."))
    index = index.loc[
        (index['directory'] == True) | (index['path'].str.endswith('.py'))
    ]
    if gitignore is True:
        cmd = Viewer.from_command('git', 'ls-files')
        cmd.wait()
        repo_files = []
        for line in cmd.out:
            repo_files += line.splitlines()
        index = index.loc[
            (index['directory'] == True)
            | index['path'].isin(repo_files)
        ]
    tf = make_treeframe(index).reset_index(drop=True)
    name, level = root_module, -1
    modules = _get_branch(name, level, tf)
    if level + 1 in tf.columns:
        for submod in tf[level + 1]:
            modules |= _get_branch(f"{name}.{submod}", level + 1, tf)
    return modules


def branch_to_lines(tree, level=0):
    headername = tree["module"]
    if '.' in headername:
        headername = '.'.join(headername.split('.')[1:])
    lines = [f"{'#' * min(level + 1, 3)} {headername}\n"]
    lines += [f"::: {tree['module']}"]
    lines.append('\n')
    lines += chain(
        *[
            branch_to_lines(c, level + 1) for c in tree["children"]
        ]
    )
    lines.append("\n")
    return lines


def modules_to_lines(modules):
    lines = []
    for m in sorted(modules.values(), key=lambda m: m['name']):
        headername, level = m["name"], m['name'].count('.')
        if '.' in headername:
            headername = '.'.join(headername.split('.')[1:])
        lines += [
            f"{'#' * min(level + 1, 3)} {headername}\n",
            f"::: {m['name']}",
            "\n\n"
        ]
    return lines


def write_to_markdown(lines, outpath):
    with open(outpath, "w") as stream:
        stream.write(re.sub('\n\n+', '\n\n', "\n".join(lines)))
