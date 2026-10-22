"""随机问题批量验证（鲁棒性 / 规模 / 性能）。

用法：
    python scripts/benchmark.py                  # 默认 100 个随机问题
    python scripts/benchmark.py --problems 500 --literals 12 --depth 8
    python scripts/benchmark.py --verbose        # 打印每个问题的结果

也可以直接用命令行：`btplan bench --problems 50`
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from btplan.tools.benchmark import format_report, run_benchmark  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="btplan 随机问题基准测试")
    parser.add_argument("--problems", type=int, default=100)
    parser.add_argument("--literals", type=int, default=10, help="文字总数")
    parser.add_argument("--depth", type=int, default=10, help="动作链长度")
    parser.add_argument("--iters", type=int, default=10, help="动作链条数")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    result = run_benchmark(
        problems=args.problems,
        literals_num=args.literals,
        depth=args.depth,
        iters=args.iters,
        seed=args.seed,
        verbose=args.verbose,
    )
    print(format_report(result))
    return 0 if result.solved == result.total else 1


if __name__ == "__main__":
    raise SystemExit(main())
