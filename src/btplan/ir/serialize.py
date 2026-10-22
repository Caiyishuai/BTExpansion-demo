"""IR → PTML 文本。

PTML 是行为树的文本表示，方便存档、diff 和人工检查：

    selector{
    cond At(b,ab)
    sequence{
    cond Free(ab)
    cond WayClear
    act Move(b,ab)
    }
    }

读法：selector 里任一分支成立即成立；sequence 里要全部成立。
多个文字组成的条件写成 sequence{cond A cond B}，表示 A 与 B 都要成立。
"""

from __future__ import annotations

from btplan.ir.node import ACTION, CONDITION, SELECTOR, SEQUENCE, BTNode


def to_ptml(node: BTNode) -> str:
    """把 IR 树序列化成 PTML 字符串。"""
    if node.node_type == SELECTOR:
        return "selector{\n" + "".join(to_ptml(c) for c in node.children) + "}\n"
    if node.node_type == SEQUENCE:
        return "sequence{\n" + "".join(to_ptml(c) for c in node.children) + "}\n"
    if node.node_type == ACTION:
        return f"act {node.action.name}\n"
    if node.node_type == CONDITION:
        return _condition_to_ptml(node)
    raise ValueError(f"未知节点类型：{node.node_type}")


def _condition_to_ptml(node: BTNode) -> str:
    literals = sorted(map(str, node.literals))
    if not literals:
        return "cond true\n"
    if len(literals) == 1:
        return f"cond {literals[0]}\n"
    body = "".join(f"cond {x}\n" for x in literals)
    return f"sequence{{\n{body}}}\n"
