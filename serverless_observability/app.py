#!/usr/bin/env python3
"""软考教学用 Serverless/FaaS 运行时模拟器，只使用 Python 标准库。"""

from __future__ import annotations

import json
import os
import random
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, urlparse


HOST = "0.0.0.0"
PORT = 8080
DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).parent / "runtime_data"))
DB_PATH = DATA_DIR / "payments.db"
LOG_PATH = DATA_DIR / "application.jsonl"
TRACE_PATH = DATA_DIR / "traces.jsonl"
DLQ_PATH = DATA_DIR / "dead_letter_queue.jsonl"
SCALE_TO_ZERO_SECONDS = int(os.getenv("SCALE_TO_ZERO_SECONDS", "8"))
MAX_INSTANCES = int(os.getenv("MAX_INSTANCES", "8"))
PROVISIONED_INSTANCES = int(os.getenv("PROVISIONED_INSTANCES", "0"))
if not 0 <= PROVISIONED_INSTANCES <= MAX_INSTANCES:
    raise ValueError("PROVISIONED_INSTANCES 必须在 0 和 MAX_INSTANCES 之间")

DATA_DIR.mkdir(parents=True, exist_ok=True)
IO_LOCK = threading.Lock()

METRICS: dict[str, float] = {
    "requests_total": 0,
    "requests_failed_total": 0,
    "cold_starts_total": 0,
    "cold_start_duration_ms_sum": 0,
    "scale_out_total": 0,
    "retries_total": 0,
    "dlq_messages_total": 0,
    "request_duration_ms_sum": 0,
}
METRICS_LOCK = threading.Lock()


def metric_add(name: str, value: float = 1) -> None:
    with METRICS_LOCK:
        METRICS[name] += value


def write_json_line(path: Path, record: dict[str, Any]) -> None:
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with IO_LOCK:
        with path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")


def log(level: str, message: str, **fields: Any) -> None:
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "level": level,
        "service": "serverless-runtime",
        "message": message,
        **fields,
    }
    print(json.dumps(record, ensure_ascii=False), flush=True)
    write_json_line(LOG_PATH, record)


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    service: str
    operation: str
    start_ms: int
    duration_ms: int
    status: str
    attributes: dict[str, Any]


@contextmanager
def span(trace_id: str, service: str, operation: str,
         parent_span_id: str | None = None, **attributes: Any) -> Iterator[str]:
    span_id = uuid.uuid4().hex[:16]
    start = time.time()
    status = "OK"
    try:
        yield span_id
    except Exception:
        status = "ERROR"
        raise
    finally:
        item = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            service=service,
            operation=operation,
            start_ms=int(start * 1000),
            duration_ms=int((time.time() - start) * 1000),
            status=status,
            attributes=attributes,
        )
        write_json_line(TRACE_PATH, asdict(item))


class FunctionRuntime:
    """模拟按并发扩容的函数实例，以及空闲后缩容到零。"""

    def __init__(self) -> None:
        self.instances = PROVISIONED_INSTANCES
        self.in_flight = 0
        self.last_activity = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, trace_id: str) -> tuple[int, bool]:
        cold_start = False
        with self.lock:
            if self.instances == 0:
                self.instances = 1
                cold_start = True
                metric_add("cold_starts_total")
                log("INFO", "cold start", trace_id=trace_id, instances=self.instances)
            elif self.in_flight >= self.instances and self.instances < MAX_INSTANCES:
                self.instances += 1
                metric_add("scale_out_total")
                log("INFO", "scale out", trace_id=trace_id, instances=self.instances)
            self.in_flight += 1
            self.last_activity = time.monotonic()
            instance = min(self.in_flight, self.instances)

        if cold_start:
            self.simulate_cold_start(trace_id)
        return instance, cold_start

    @staticmethod
    def simulate_cold_start(trace_id: str) -> None:
        """把冷启动拆成可观测阶段，便于定位启动瓶颈。"""
        started = time.time()
        with span(trace_id, "serverless-platform", "cold-start") as cold_span_id:
            with span(trace_id, "serverless-platform", "allocate-sandbox", cold_span_id):
                time.sleep(0.08)  # 分配容器/微虚拟机、网络和资源
            with span(trace_id, "language-runtime", "load-runtime", cold_span_id):
                time.sleep(0.12)  # 启动 Python/JVM/Node 等语言运行时
            with span(trace_id, "user-function", "initialize-code", cold_span_id):
                time.sleep(0.15)  # 解压代码、导入依赖、执行全局初始化
        duration_ms = int((time.time() - started) * 1000)
        metric_add("cold_start_duration_ms_sum", duration_ms)
        log("INFO", "cold start phases completed", trace_id=trace_id,
            duration_ms=duration_ms)

    def release(self) -> None:
        with self.lock:
            self.in_flight -= 1
            self.last_activity = time.monotonic()

    def state(self) -> dict[str, int]:
        with self.lock:
            return {
                "instances": self.instances,
                "in_flight": self.in_flight,
                "provisioned_instances": PROVISIONED_INSTANCES,
            }

    def reap_idle_instances(self) -> None:
        while True:
            time.sleep(1)
            with self.lock:
                idle = time.monotonic() - self.last_activity
                if (self.instances > PROVISIONED_INSTANCES and self.in_flight == 0
                        and idle >= SCALE_TO_ZERO_SECONDS):
                    previous = self.instances
                    self.instances = PROVISIONED_INSTANCES
                    log("INFO", "scale in after idle", previous_instances=previous,
                        remaining_instances=PROVISIONED_INSTANCES)


RUNTIME = FunctionRuntime()


def initialize_database() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS payments (
                   request_id TEXT PRIMARY KEY,
                   user_id TEXT NOT NULL,
                   amount REAL NOT NULL CHECK (amount > 0),
                   created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
               )"""
        )


def charge_function(payload: dict[str, Any], trace_id: str,
                    parent_span_id: str) -> dict[str, Any]:
    request_id = str(payload.get("request_id", ""))
    user_id = str(payload.get("user_id", ""))
    amount = float(payload.get("amount", 0))
    if not request_id or not user_id or amount <= 0:
        raise ValueError("request_id、user_id 必填，amount 必须大于 0")

    with span(trace_id, "payment-function", "charge", parent_span_id,
              request_id=request_id) as function_span_id:
        time.sleep(0.04)
        with span(trace_id, "managed-database", "insert-payment", function_span_id):
            with sqlite3.connect(DB_PATH) as connection:
                try:
                    connection.execute(
                        "INSERT INTO payments(request_id, user_id, amount) VALUES (?, ?, ?)",
                        (request_id, user_id, amount),
                    )
                    created = True
                except sqlite3.IntegrityError:
                    created = False  # request_id 唯一约束实现幂等
        return {
            "status": "charged" if created else "already_processed",
            "request_id": request_id,
            "amount": amount,
        }


def promotion_function(user_id: str, trace_id: str, parent_span_id: str,
                       force_failure: bool) -> dict[str, Any]:
    with span(trace_id, "promotion-function", "calculate-discount", parent_span_id,
              user_id=user_id):
        time.sleep(random.uniform(0.08, 0.18))
        if force_failure:
            raise RuntimeError("模拟下游优惠规则服务不可用")
        discount = 20 if sum(user_id.encode("utf-8")) % 3 == 0 else 10
        return {"user_id": user_id, "discount_percent": discount}


def invoke_with_retry(function_name: str, invocation: Any, event: dict[str, Any],
                      trace_id: str, max_attempts: int = 3) -> dict[str, Any]:
    for attempt in range(1, max_attempts + 1):
        try:
            return invocation()
        except Exception as exc:
            log("ERROR", "function invocation failed", trace_id=trace_id,
                function=function_name, attempt=attempt, error=str(exc))
            if attempt < max_attempts:
                metric_add("retries_total")
                time.sleep(0.05 * attempt)
                continue
            dlq_record = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "trace_id": trace_id,
                "function": function_name,
                "event": event,
                "error": str(exc),
            }
            write_json_line(DLQ_PATH, dlq_record)
            metric_add("dlq_messages_total")
            raise
    raise AssertionError("unreachable")


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "ServerlessExamDemo/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return  # 使用上面的结构化日志代替默认访问日志

    def send_json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json(HTTPStatus.OK, {"status": "UP"})
            return
        if parsed.path == "/runtime":
            self.send_json(HTTPStatus.OK, {
                **RUNTIME.state(),
                "scale_to_zero_seconds": SCALE_TO_ZERO_SECONDS,
                "max_instances": MAX_INSTANCES,
            })
            return
        if parsed.path == "/metrics":
            with METRICS_LOCK:
                values = dict(METRICS)
            values.update(RUNTIME.state())
            self.send_json(HTTPStatus.OK, values)
            return
        if parsed.path == "/api/promotion":
            query = parse_qs(parsed.query)
            user_id = query.get("user_id", ["anonymous"])[0]
            force_failure = query.get("fail", ["0"])[0] == "1"
            self.handle_invocation(
                "promotion-function",
                {"user_id": user_id, "force_failure": force_failure},
                lambda trace_id, parent_id: promotion_function(
                    user_id, trace_id, parent_id, force_failure
                ),
            )
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/charge":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            payload = self.read_json()
        except (json.JSONDecodeError, ValueError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})
            return
        self.handle_invocation(
            "payment-function",
            payload,
            lambda trace_id, parent_id: charge_function(payload, trace_id, parent_id),
        )

    def handle_invocation(self, function_name: str, event: dict[str, Any],
                          invocation: Any) -> None:
        trace_id = self.headers.get("X-Trace-Id", uuid.uuid4().hex)
        started = time.time()
        instance, cold_start = RUNTIME.acquire(trace_id)
        metric_add("requests_total")
        try:
            with span(trace_id, "api-gateway", f"invoke:{function_name}",
                      method=self.command, path=self.path) as gateway_span_id:
                result = invoke_with_retry(
                    function_name,
                    lambda: invocation(trace_id, gateway_span_id),
                    event,
                    trace_id,
                )
            duration_ms = int((time.time() - started) * 1000)
            metric_add("request_duration_ms_sum", duration_ms)
            log("INFO", "request completed", trace_id=trace_id,
                function=function_name, instance=instance, cold_start=cold_start,
                duration_ms=duration_ms)
            self.send_json(HTTPStatus.OK, {
                "trace_id": trace_id,
                "instance": instance,
                "cold_start": cold_start,
                "result": result,
            })
        except ValueError as exc:
            metric_add("requests_failed_total")
            self.send_json(HTTPStatus.BAD_REQUEST, {"trace_id": trace_id, "error": str(exc)})
        except Exception as exc:
            metric_add("requests_failed_total")
            self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {
                "trace_id": trace_id,
                "error": str(exc),
                "dead_lettered": True,
            })
        finally:
            RUNTIME.release()


def main() -> None:
    initialize_database()
    threading.Thread(target=RUNTIME.reap_idle_instances, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    log("INFO", "runtime started", host=HOST, port=PORT,
        scale_to_zero_seconds=SCALE_TO_ZERO_SECONDS, max_instances=MAX_INSTANCES,
        provisioned_instances=PROVISIONED_INSTANCES)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

