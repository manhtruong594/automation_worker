# WorkAI curl transport

Chỉ dùng `curl.exe` để gọi `https://workai-be.horusjsc.com/api`. Trên PowerShell, `curl` có thể là alias nên luôn ghi `curl.exe`. Nếu dùng Python để điều phối batch, gọi binary bằng `subprocess.run(..., shell=False)`, không dùng HTTP client của Python.

Credential đi qua stdin của `curl.exe --config -`, không nằm trong command line. JSON request và response nằm trong thư mục tạm, được xóa khi hàm kết thúc. Không in config, body request, token/cookie hoặc response chứa dữ liệu nhạy cảm vào log.

```python
import json
import os
import subprocess
import tempfile
from pathlib import Path

BASE_URL = "https://workai-be.horusjsc.com/api"


def _curl_config_value(value):
    if "\r" in value or "\n" in value:
        raise ValueError("Invalid credential")
    return value.replace("\\", "\\\\").replace('"', '\\"')


def workai_request(method, path, payload=None, timeout=60):
    if method not in {"GET", "POST", "PUT"} or not path.startswith("/"):
        raise ValueError("Invalid WorkAI request")
    token = os.environ.get("WORKAI_TOKEN")
    session = os.environ.get("WORKAI_SESSION_TOKEN")
    if token:
        config = f'header = "Authorization: Bearer {_curl_config_value(token)}"\n'
    elif session:
        config = f'header = "Cookie: sessionToken={_curl_config_value(session)}"\n'
    else:
        raise RuntimeError("WORKAI_TOKEN or WORKAI_SESSION_TOKEN is required")

    with tempfile.TemporaryDirectory() as temp_dir:
        response_file = Path(temp_dir) / "response"
        command = [
            "curl.exe", "-q", "--config", "-", "--silent", "--show-error",
            "--request", method, "--max-time", str(timeout),
            "--header", "Accept: application/json",
            "--output", str(response_file),
            "--write-out", "%{http_code}\\n%header{cf-ray}",
        ]
        if payload is not None:
            request_file = Path(temp_dir) / "request.json"
            request_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            command += ["--header", "Content-Type: application/json",
                        "--data-binary", f"@{request_file}"]
        command.append(BASE_URL + path)
        result = subprocess.run(command, input=config, text=True, encoding="utf-8",
                                capture_output=True, shell=False, timeout=timeout + 5)
        status_line, _, ray_id = result.stdout.partition("\n")
        status = int(status_line) if status_line.isdigit() else 0
        body = response_file.read_text(encoding="utf-8", errors="replace") if response_file.exists() else ""
        return status, ray_id.strip(), body, result.returncode
```

Trước mọi mutation, gọi `workai_request("GET", "/time-allocations?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD")` cho một tuần liên quan, xác nhận `returncode == 0`, HTTP `2xx` và body là JSON WorkAI có `success == true` cùng `meta.user_id`. Dùng hàm này cho mọi request tiếp theo. Endpoint gợi ý nội dung dùng `timeout=30`; các timeout mutation cần xử lý theo mục **Retry Sau Timeout Hoặc Lỗi Mơ Hồ** trong `SKILL.md`.

Luôn kiểm tra HTTP status trước khi parse JSON. `403` kèm HTML Cloudflare/Error `1010` là lỗi ở lớp Cloudflare; ghi status và `ray_id`, dừng batch. `401` hoặc JSON WorkAI `UNAUTHENTICATED` mới là lỗi xác thực WorkAI. Với lỗi `curl.exe` (return code khác 0), báo lỗi mạng/TLS/timeout theo stderr đã loại bỏ dữ liệu nhạy cảm; không kết luận mutation chưa xảy ra.
