import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import stt
from stt import Recorder
from llm import generate_user_story

HOST = "127.0.0.1"
PORT = 8000
INDEX = Path(__file__).parent / "index.html"

recorder = Recorder()


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = INDEX.read_text(encoding="utf-8").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            if self.path == "/api/start":
                recorder.start()
                self._send_json({"ok": True})

            elif self.path == "/api/stop":
                transcript = recorder.stop()
                self._send_json({"transcript": transcript})

            elif self.path == "/api/generate":
                data = self._read_json()
                transcript = (data.get("transcript") or "").strip()
                if not transcript:
                    self._send_json({"error": "No transcript provided."}, 400)
                    return
                story = generate_user_story(transcript)
                self._send_json({"story": story})

            else:
                self._send_json({"error": "Not found"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def log_message(self, *args):
        pass  # keep the console clean


def main():
    print("Warming up the speech model...", flush=True)
    stt.warm_up()

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"\nVoice to User Story is running.")
    print(f"Open  http://{HOST}:{PORT}  in your browser.")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
