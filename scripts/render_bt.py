"""把 PDDL 生成的行为树渲染成图片（SVG / PNG）。

用法:
  # 渲染单个样例，图片写到样例目录
  python scripts/render_bt.py pddl/minimal/domain.pddl pddl/minimal/problem.pddl

  # 指定输出前缀（会生成 <prefix>.svg 与 <prefix>.png）
  python scripts/render_bt.py pddl/movebtob/domain.pddl pddl/movebtob/problem.pddl \
         -o pddl/movebtob/bt

  # 一次渲染全部内置样例
  python scripts/render_bt.py --all

依赖: graphviz 的 dot 命令（无需 python graphviz 包）。

节点样式约定（与 pddl/ADMISSIBILITY.md 的配色一致）:
  ?  Selector  蓝   —— 回退：依次尝试直到成功
  >  Sequence  绿   —— 顺序：依次执行直到失败
  cond        琥珀  —— 条件守卫（命题集合）
  act         粉    —— 动作
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from pddl_adapter import load_domain, load_problem, ground          # noqa: E402
from bt_expansion.algorithm import BTExpAlgorithm                    # noqa: E402

PDDL_DIR = os.path.join(PROJECT_ROOT, 'pddl')

# 内置样例（由简单到复杂）
# (目录名, 描述, 条件显示行数上限或 None=不限, 是否用紧凑布局)
SAMPLES = [
    ('movebtob',     '最简：对拍基准，9 结点',                 None, False),
    ('minimal',      '最小模板：3 动作 / 3 对象',              None, False),
    ('neg_precond',  '负前提：自动补谓词编码',                 None, False),
    ('cond_effects', '条件效果：分支 add 的守卫',              None, False),
    ('robot_fetch',  'lifted+types：15 动作 → 71 结点',        2,    True),
]

FONT = 'Helvetica'

STYLE = {
    '?':    ('?',  'box',     '#E6F1FB', '#185FA5'),   # Selector
    '>':    ('→', 'box',     '#EAF3DE', '#3B6D11'),   # Sequence
    'cond': (None, 'ellipse', '#FAEEDA', '#854F0B'),
    'act':  (None, 'box',     '#FBEAF0', '#993556'),
}


def _esc(text: str) -> str:
    return text.replace('\\', '\\\\').replace('"', '\\"')


def _cond_label(content, max_lines=None) -> str:
    """条件节点：内容是命题集合，多个文字分行显示。

    max_lines 限制显示行数（超出用 … 省略），用于把过宽的树收窄到可读。
    图片只是概览，完整条件集合仍可从导出的 PTML / 树对象中获取。
    """
    items = sorted(str(x) for x in content)
    if not items:
        return '(true)'
    if max_lines and len(items) > max_lines:
        items = items[:max_lines] + ['… +%d' % (len(items) - max_lines)]
    return '\\n'.join(_esc(i) for i in items)


def _act_label(action) -> str:
    return _esc(getattr(action, 'name', str(action)))


def build_dot(root, max_cond_lines=None, compact=False) -> str:
    """遍历行为树，生成 DOT 源码。root 为 ControlBT / Leaf。"""
    nodesep = 0.10 if compact else 0.22
    ranksep = 0.30 if compact else 0.45
    fsize = 9 if compact else 11
    lines = [
        'digraph BT {',
        '  rankdir=TB;',
        '  bgcolor="white";',
        f'  fontname="{FONT}";',
        '  node [fontname="%s" fontsize=%d style="rounded,filled" '
        'penwidth=1.2];' % (FONT, fsize),
        '  edge [color="#888780" penwidth=1.0 arrowsize=0.7];',
        '  nodesep=%s; ranksep=%s;' % (nodesep, ranksep),
    ]
    counter = [0]

    def emit(node):
        nid = 'n%d' % counter[0]
        counter[0] += 1

        if hasattr(node, 'children'):                     # ControlBT
            head, shape, fill, stroke = STYLE.get(node.type, ('?', 'box', '#F1EFE8', '#5F5E5A'))
            label = head
        else:                                             # Leaf
            _, shape, fill, stroke = STYLE.get(node.type, ('?', 'box', '#F1EFE8', '#5F5E5A'))
            label = (_cond_label(node.content, max_cond_lines) if node.type == 'cond'
                     else _act_label(node.content))

        lines.append(
            '  %s [label="%s" shape=%s fillcolor="%s" color="%s" fontcolor="#2C2C2A"];'
            % (nid, label, shape, fill, stroke))

        for child in getattr(node, 'children', []):
            cid = emit(child)
            lines.append('  %s -> %s;' % (nid, cid))
        return nid

    # 算法返回的根是只有一个 child 的 Selector，从 children[0] 起画更干净
    start = root.children[0] if getattr(root, 'children', None) and len(root.children) == 1 else root
    emit(start)
    lines.append('}')
    return '\n'.join(lines)


def render(domain_path, problem_path, out_prefix, title=None,
           max_cond_lines=None, compact=False):
    """生成行为树并渲染为 svg + png，返回 (树结点数, dot 源码)。"""
    dom, prob = load_domain(domain_path), load_problem(problem_path)
    g = ground(dom, prob)
    goal, start, actions = g.as_tuple()

    algo = BTExpAlgorithm(verbose=False)
    algo.clear()
    bt = algo.run_algorithm_selTree(start, goal, actions)
    if bt is False or bt is None:
        raise RuntimeError('算法返回 Failure：该目标在给定动作集下不可达')

    dot = build_dot(bt, max_cond_lines, compact)
    dot_path = out_prefix + '.dot'
    with open(dot_path, 'w', encoding='utf-8') as fh:
        fh.write(dot)

    for fmt in ('svg', 'png'):
        cmd = ['dot', '-T' + fmt, dot_path, '-o', out_prefix + '.' + fmt]
        if fmt == 'png':
            cmd[1:1] = ['-Gdpi=144']
        subprocess.run(cmd, check=True)

    size = bt.count_size() - 1
    print('  %-34s 结点 %3d  ->  %s.svg / %s.png'
          % (title or os.path.basename(out_prefix), size, out_prefix, out_prefix))
    return size, dot


def main():
    ap = argparse.ArgumentParser(description='把 PDDL 生成的行为树渲染成图片')
    ap.add_argument('domain', nargs='?', help='domain.pddl 路径')
    ap.add_argument('problem', nargs='?', help='problem.pddl 路径')
    ap.add_argument('-o', '--output', default=None, help='输出前缀（不含扩展名）')
    ap.add_argument('--all', action='store_true', help='渲染全部内置样例')
    ap.add_argument('--cond-lines', type=int, default=None,
                    help='条件节点最多显示的行数（超出用 … 省略），用于收窄过宽的树')
    args = ap.parse_args()

    if not args.all and not (args.domain and args.problem):
        ap.error('需要 domain + problem，或使用 --all')

    try:
        subprocess.run(['dot', '-V'], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        print('错误: 未找到 graphviz 的 dot 命令。请先安装，例如 brew install graphviz',
              file=sys.stderr)
        return 1

    if args.all:
        print('渲染全部内置样例（由简单到复杂）:')
        for name, desc, cond_lines, compact in SAMPLES:
            render(os.path.join(PDDL_DIR, name, 'domain.pddl'),
                   os.path.join(PDDL_DIR, name, 'problem.pddl'),
                   os.path.join(PDDL_DIR, name, 'bt'),
                   title='%s (%s)' % (name, desc),
                   max_cond_lines=cond_lines, compact=compact)
        print('完成。')
        return 0

    out = args.output or os.path.splitext(args.problem)[0]
    render(args.domain, args.problem, out, max_cond_lines=args.cond_lines)
    return 0


if __name__ == '__main__':
    sys.exit(main())
