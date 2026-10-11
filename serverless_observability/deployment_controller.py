#!/usr/bin/env python3
"""演示不可变基础设施和声明式 API 的最小控制器。"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DESIRED_PATH = BASE_DIR / "infra" / "desired_state.json"
REGISTRY_PATH = BASE_DIR / "infra" / "image_registry.json"
ACTUAL_PATH = BASE_DIR / "infra" / "actual_state.json"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists() and default is not None:
        return copy.deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate(desired: dict[str, Any], registry: dict[str, str]) -> None:
    image = desired.get("image")
    digest = desired.get("digest")
    if image not in registry:
        raise ValueError(f"镜像 {image!r} 不在已批准的镜像仓库中")
    if registry[image] != digest:
        raise ValueError(
            "镜像标签与摘要不匹配：同一个版本禁止被覆盖，部署必须引用不可变 digest"
        )
    replicas = desired.get("replicas")
    if not isinstance(replicas, int) or replicas < 0:
        raise ValueError("replicas 必须是非负整数")


def reconcile(desired: dict[str, Any], actual: dict[str, Any],
              registry: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    """比较期望状态和实际状态，通过替换资源收敛，而不是登录机器修改。"""
    validate(desired, registry)
    actions: list[str] = []
    old_digest = actual.get("digest")

    if old_digest != desired["digest"]:
        if old_digest:
            actions.append(f"创建使用 {desired['image']} 的新实例")
            actions.append("健康检查通过后切换流量")
            actions.append("删除旧实例；不在旧实例上执行 SSH 升级")
        else:
            actions.append(f"创建使用 {desired['image']} 的实例")

    if actual.get("replicas") != desired["replicas"]:
        actions.append(
            f"副本数从 {actual.get('replicas', 0)} 调整为 {desired['replicas']}"
        )

    if actual.get("environment") != desired.get("environment", {}):
        actions.append("配置发生变化：替换实例使新配置生效")

    if not actions:
        actions.append("实际状态已经符合期望状态，无需操作（幂等）")

    generation = actual.get("generation", 0)
    changed = any("无需操作" not in action for action in actions)
    new_actual = {
        **desired,
        "generation": generation + 1 if changed else generation,
        "ready_replicas": desired["replicas"],
    }
    return new_actual, actions


def print_step(name: str, desired: dict[str, Any], actual: dict[str, Any],
               registry: dict[str, str]) -> dict[str, Any]:
    print(f"\n=== {name} ===")
    new_actual, actions = reconcile(desired, actual, registry)
    print("期望状态：", json.dumps(desired, ensure_ascii=False))
    for action in actions:
        print("-", action)
    print("实际状态：", json.dumps(new_actual, ensure_ascii=False))
    return new_actual


def demo() -> None:
    registry = read_json(REGISTRY_PATH)
    v1 = read_json(DESIRED_PATH)
    actual: dict[str, Any] = {}

    actual = print_step("首次部署 v1", v1, actual, registry)
    actual = print_step("重复提交相同期望状态", v1, actual, registry)

    v2 = {
        **v1,
        "image": "charging-functions:1.1.0",
        "digest": registry["charging-functions:1.1.0"],
        "replicas": 4,
    }
    actual = print_step("发布 v2：创建新资源并替换旧资源", v2, actual, registry)
    actual = print_step("回滚 v1：重新创建旧版本资源", v1, actual, registry)
    print("\n整个过程只修改声明并由控制器收敛，没有 SSH 登录实例修改软件。")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["reconcile", "status", "demo"], nargs="?",
                        default="demo")
    args = parser.parse_args()
    if args.command == "demo":
        demo()
        return
    if args.command == "status":
        print(json.dumps(read_json(ACTUAL_PATH, {}), ensure_ascii=False, indent=2))
        return

    desired = read_json(DESIRED_PATH)
    actual = read_json(ACTUAL_PATH, {})
    registry = read_json(REGISTRY_PATH)
    new_actual, actions = reconcile(desired, actual, registry)
    write_json(ACTUAL_PATH, new_actual)
    for action in actions:
        print("-", action)
    print(f"实际状态已保存到 {ACTUAL_PATH}")


if __name__ == "__main__":
    main()
