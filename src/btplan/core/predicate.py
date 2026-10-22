"""符号文字的解析与格式化。

规划里到处都是 ``"At(b,ab)"`` 这样的字符串。py_trees 节点需要把它拆成
"类名 + 参数"，才能造出对应的节点对象：

    "At(b,ab)"  ->  ("At", ("b", "ab"))   ->  At("b", "ab")
"""

from __future__ import annotations

import re
from typing import Tuple

_PREDICATE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*$")


def parse_predicate(text: str) -> Tuple[str, Tuple[str, ...]]:
    """把一个符号文字拆成 ``(类名, 参数元组)``。

    >>> parse_predicate("At(b,ab)")
    ('At', ('b', 'ab'))
    >>> parse_predicate("WayClear")
    ('WayClear', ())
    """
    match = _PREDICATE_RE.match(text or "")
    if not match:
        return (text or "").strip(), ()
    args = tuple(a.strip() for a in match.group(2).split(",") if a.strip())
    return match.group(1), args


def format_predicate(name: str, args=()) -> str:
    """把 ``(类名, 参数)`` 拼回符号文字。

    无参数时保持"裸文字"写法，与状态里的拼写一致：

    >>> format_predicate("At", ("b", "ab"))
    'At(b,ab)'
    >>> format_predicate("WayClear")
    'WayClear'
    """
    if not args:
        return name
    return f"{name}({','.join(str(a) for a in args)})"
