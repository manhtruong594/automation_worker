#!/usr/bin/env python3
"""Complete one or more WorkAI issues with preflight and verification."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://workai-be.horus.io.vn/api"
TRANSITION_ID = "wf_in_progress_done"
DONE_VALUES = {
    "done",
    "completed",
    "complete",
    "hoan thanh",
    "hoàn thành",
    "wf in progress done",
}


@dataclass
class ApiResult:
    ok: bool
    status: int | None
    body: Any
    error: str | None = None
    ambiguous: bool = False


def _json_or_text(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _request(method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None, timeout: float) -> ApiResult:
    data = None
    request_headers = dict(headers)
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return ApiResult(True, response.status, _json_or_text(response.read()))
    except HTTPError as exc:
        return ApiResult(False, exc.code, _json_or_text(exc.read()), str(exc))
    except (TimeoutError, socket.timeout) as exc:
        return ApiResult(False, None, None, str(exc), ambiguous=True)
    except URLError as exc:
        return ApiResult(False, None, None, str(exc.reason), ambiguous=method != "GET")
    except OSError as exc:
        return ApiResult(False, None, None, str(exc), ambiguous=method != "GET")


def _data(body: Any) -> Any:
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _status_value(body: Any) -> str | None:
    item = _data(body)
    if not isinstance(item, dict):
        return None
    status = item.get("status")
    if isinstance(status, dict):
        for key in ("name", "label", "value", "key", "id"):
            if status.get(key) is not None:
                return str(status[key])
        return None
    return str(status) if status is not None else None


def _normalized(value: str | None) -> str:
    return " ".join((value or "").strip().lower().replace("_", " ").replace("-", " ").split())


def _is_done(body: Any) -> bool:
    return _normalized(_status_value(body)) in DONE_VALUES


def _error_detail(result: ApiResult) -> dict[str, Any]:
    detail: dict[str, Any] = {"http_status": result.status}
    body = result.body
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict):
        if error.get("code") is not None:
            detail["code"] = error["code"]
        if error.get("message") is not None:
            detail["message"] = error["message"]
    elif body is not None:
        detail["response"] = body
    if result.error and "message" not in detail:
        detail["message"] = result.error
    return detail


def _issue_url(base_url: str, issue_id: int) -> str:
    return f"{base_url.rstrip('/')}/issues/{quote(str(issue_id), safe='')}"


def _read_issue(base_url: str, issue_id: int, headers: dict[str, str], timeout: float) -> ApiResult:
    return _request("GET", _issue_url(base_url, issue_id), headers, None, timeout)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-id", action="append", required=True, help="Positive integer; repeat for a batch")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds (default: 30)")
    return parser.parse_args()


def _auth_headers() -> dict[str, str]:
    token = os.environ.get("WORKAI_TOKEN")
    session_token = os.environ.get("WORKAI_SESSION_TOKEN")
    headers = {"Accept": "application/json", "User-Agent": "workai-complete-issues-api/1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif session_token:
        headers["Cookie"] = f"sessionToken={session_token}"
    else:
        raise ValueError("Set WORKAI_TOKEN or WORKAI_SESSION_TOKEN before running this helper.")
    return headers


def main() -> int:
    args = _parse_args()
    if args.timeout <= 0:
        print(json.dumps({"phase": "validation", "error": "--timeout must be positive."}))
        return 2

    parsed: list[int] = []
    invalid: list[dict[str, Any]] = []
    for position, raw in enumerate(args.issue_id, start=1):
        try:
            issue_id = int(raw)
            if issue_id <= 0 or str(issue_id) != raw.strip():
                raise ValueError
            parsed.append(issue_id)
        except ValueError:
            invalid.append({"position": position, "value": raw})
    if invalid:
        print(json.dumps({"phase": "validation", "invalid_issue_ids": invalid}, ensure_ascii=False))
        return 2

    unique_ids = list(dict.fromkeys(parsed))
    duplicates = [
        {"position": index, "issue_id": issue_id, "first_position": parsed.index(issue_id) + 1}
        for index, issue_id in enumerate(parsed, start=1)
        if parsed.index(issue_id) + 1 != index
    ]
    try:
        headers = _auth_headers()
    except ValueError as exc:
        print(json.dumps({"phase": "auth", "error": str(exc)}))
        return 2

    preflight: dict[int, ApiResult] = {}
    preflight_failures: list[dict[str, Any]] = []
    for issue_id in unique_ids:
        result = _read_issue(args.base_url, issue_id, headers, args.timeout)
        preflight[issue_id] = result
        if not result.ok:
            preflight_failures.append({"issue_id": issue_id, **_error_detail(result)})
    if preflight_failures:
        print(json.dumps({
            "phase": "preflight",
            "mutation_started": False,
            "duplicates": duplicates,
            "failures": preflight_failures,
        }, ensure_ascii=False))
        return 2

    results: list[dict[str, Any]] = []
    stop_mutations = False
    for issue_id in unique_ids:
        before = preflight[issue_id]
        if _is_done(before.body):
            results.append({"issue_id": issue_id, "result": "already_completed", "server_status": _status_value(before.body)})
            continue
        if stop_mutations:
            results.append({"issue_id": issue_id, "result": "not_attempted", "reason": "auth_or_permission_failure"})
            continue

        transition_url = f"{_issue_url(args.base_url, issue_id)}/transition"
        transition = _request("POST", transition_url, headers, {"transition_id": TRANSITION_ID}, args.timeout)
        verification = _read_issue(args.base_url, issue_id, headers, args.timeout)
        if verification.ok and _is_done(verification.body):
            results.append({
                "issue_id": issue_id,
                "result": "completed",
                "server_status": _status_value(verification.body),
                "transition_http_status": transition.status,
            })
            continue

        item: dict[str, Any] = {
            "issue_id": issue_id,
            "result": "failed",
            "transition_sent": transition.ok or transition.ambiguous,
            "verified_completed": False,
        }
        if not transition.ok:
            item["transition_error"] = _error_detail(transition)
        if not verification.ok:
            item["verification_error"] = _error_detail(verification)
        else:
            item["server_status"] = _status_value(verification.body)
        results.append(item)
        if transition.status in (401, 403) or verification.status in (401, 403):
            stop_mutations = True

    failed = sum(item["result"] in {"failed", "not_attempted"} for item in results)
    print(json.dumps({
        "phase": "complete",
        "transition_id": TRANSITION_ID,
        "duplicates": duplicates,
        "results": results,
        "summary": {
            "unique_issue_count": len(unique_ids),
            "completed": sum(item["result"] == "completed" for item in results),
            "already_completed": sum(item["result"] == "already_completed" for item in results),
            "failed": sum(item["result"] == "failed" for item in results),
            "not_attempted": sum(item["result"] == "not_attempted" for item in results),
        },
    }, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
