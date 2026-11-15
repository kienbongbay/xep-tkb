"""Máy chủ web chỉ dùng thư viện có sẵn của Python: phát file trong thư mục web/
và nhận yêu cầu xếp lịch tại /api/schedule."""
import json
import mimetypes
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .service import BadInput, solve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")
FIRST_PORT = 8000

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")


def resolve_static(url_path):
    """Đổi đường dẫn URL thành file trong web/. Trả về None nếu không hợp lệ
    hoặc cố thoát ra ngoài thư mục web (ví dụ ../main.py)."""
    rel = url_path.lstrip("/") or "index.html"
    full = os.path.realpath(os.path.join(WEB_DIR, rel))
    base = os.path.realpath(WEB_DIR)
    if full != base and not full.startswith(base + os.sep):
        return None
    return full if os.path.isfile(full) else None


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, obj):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        full = resolve_static(path)
        if full is None:
            msg = "Không tìm thấy trang này. Hãy giữ nguyên cấu trúc thư mục: server.py nằm cạnh thư mục web."
            self._send(404, msg.encode("utf-8"), "text/plain; charset=utf-8")
            return
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "text/javascript"):
            ctype += "; charset=utf-8"
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/schedule":
            self._json(404, {"error": "Không tìm thấy."})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            self._json(400, {"error": "Dữ liệu gửi lên không hợp lệ."})
            return
        try:
            self._json(200, solve(data))
        except BadInput as e:
            self._json(400, {"error": str(e)})
        except Exception as e:  # lỗi bất ngờ trong thuật toán: báo cho trang thay vì treo
            self._json(500, {"error": f"Lỗi khi xếp lịch: {e}"})

    def log_message(self, fmt, *args):
        print("  " + (fmt % args))


def make_server():
    for port in range(FIRST_PORT, FIRST_PORT + 20):
        try:
            return ThreadingHTTPServer(("127.0.0.1", port), Handler), port
        except OSError:
            continue
    raise SystemExit("Không mở được cổng nào từ %d đến %d. Hãy tắt chương trình đang chiếm cổng."
                     % (FIRST_PORT, FIRST_PORT + 19))


def run():
    if not os.path.exists(os.path.join(WEB_DIR, "index.html")):
        raise SystemExit("Không thấy web/index.html. Giữ nguyên cấu trúc: server.py nằm cạnh thư mục web.")
    server, port = make_server()
    url = f"http://127.0.0.1:{port}/"
    print("=" * 56)
    print(" Xếp thời khóa biểu đang chạy tại:", url)
    print(" Nhấn Ctrl+C để tắt.")
    print("=" * 56)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã tắt.")
    finally:
        server.server_close()
