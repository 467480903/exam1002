"""只读查看由 LeRobot 转换得到的 LanceDB 数据。"""

from __future__ import annotations

import argparse
from pathlib import Path

import lancedb


def main() -> None:
    parser = argparse.ArgumentParser(description="查看本地 LeRobot LanceDB 数据")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).parent / "data" / "so101_pickplace_lance",
    )
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    db = lancedb.connect(str(args.db))
    table_names = db.list_tables().tables
    print(f"数据库目录：{args.db}")
    print(f"数据表：{table_names}")

    for table_name in table_names:
        table = db.open_table(table_name)
        print(f"\n[{table_name}] 行数：{table.count_rows()}")
        print(f"字段：{table.schema.names}")

    frames = db.open_table("frames")
    columns = [
        name
        for name in ("episode_index", "frame_index", "timestamp", "task_index")
        if name in frames.schema.names
    ]
    rows = frames.search().select(columns).limit(args.limit).to_arrow()
    print("\n帧表示例：")
    print(rows)


if __name__ == "__main__":
    main()
