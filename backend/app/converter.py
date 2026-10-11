"""Presentation conversion ONLY inside the network-disabled converter container.

No Settings/database/provider credentials or private storage are imported/mounted.
The worker submits validated bytes over a permission-restricted Unix socket.
Never launch this process directly on the application host.
"""
import os
import signal
import socket
import socketserver
import stat
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

MAX_INPUT = 25 * 1024**2
MAX_OUTPUT = 100 * 1024**2
CONVERSION_SLOT = threading.BoundedSemaphore(1)


class UnixHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    address_family = socket.AF_UNIX
    daemon_threads = True

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = 'converter', 0


def convert(data, extension):
    with tempfile.TemporaryDirectory(prefix='report-') as temp:
        root = Path(temp)
        source = root / ('input.' + extension)
        source.write_bytes(data)
        command = ['/usr/bin/prlimit', '--cpu=45:45', f'--fsize={MAX_OUTPUT}:{MAX_OUTPUT}',
                   '--nofile=128:128', '--core=0:0', '--', '/usr/bin/libreoffice',
                   f'-env:UserInstallation={(root / "profile").as_uri()}',
                   '--headless', '--nologo', '--nodefault', '--nolockcheck', '--norestore',
                   '--convert-to', 'pdf:impress_pdf_Export', '--outdir', str(root), str(source)]
        process = subprocess.Popen(command, cwd=root, start_new_session=True,
                                   env={'PATH':'/usr/bin:/bin', 'HOME':temp, 'TMPDIR':'/tmp', 'LANG':'C.UTF-8'},
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            code = process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise ValueError('conversion_timeout') from None
        output = root / 'input.pdf'
        if code or not output.is_file() or output.stat().st_size > MAX_OUTPUT:
            raise ValueError('conversion_failed')
        data = output.read_bytes()
        if not data.startswith(b'%PDF-'):
            raise ValueError('conversion_failed')
        return data


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # No document/IPC metadata in logs.

    def reply(self, status, data=b'', content_type='text/plain'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.reply(200 if self.path == '/health' else 404)

    def do_POST(self):
        extension = self.headers.get('X-Document-Format', '')
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            size = 0
        if self.path != '/convert' or extension not in {'ppt','pptx'} or not 0 < size <= MAX_INPUT:
            self.reply(422)
            return
        if not CONVERSION_SLOT.acquire(blocking=False):
            self.reply(503)
            return
        try:
            self.connection.settimeout(15)
            data = self.rfile.read(size)
            if len(data) != size:
                self.reply(422)
                return
            output = convert(data, extension)
            self.reply(200, output, 'application/pdf')
        except (OSError, ValueError, subprocess.SubprocessError):
            self.reply(422)
        finally:
            CONVERSION_SLOT.release()


def main():
    if os.environ.get('CONVERTER_ISOLATED') != 'true':
        raise RuntimeError('Run only in the isolated converter container, never on the application host')
    path = Path(os.environ.get('CONVERTER_SOCKET_PATH', '/run/agritrade-converter/service.sock'))
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        if not stat.S_ISSOCK(path.stat().st_mode):
            raise RuntimeError('Converter socket path is occupied')
        path.unlink()
    with UnixHTTPServer(str(path), Handler) as server:
        path.chmod(0o600)
        server.serve_forever()


if __name__ == '__main__':
    main()
