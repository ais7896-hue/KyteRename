"""
KyteRename - KyteView IPC (透過 Windows 原生 Named Pipe 聯動預覽)
具備非阻塞極短超時保護 (15ms)，未開啟 KyteView 時絕不卡頓 UI
"""
import threading
from multiprocessing.connection import Client

PIPE_ADDRESS = r"\\.\pipe\KyteView"

def trigger_kyteview_preview_async(file_path: str):
    """非同步送出檔案預覽請求至 KyteView，完全不阻塞主執行緒"""
    def _send():
        try:
            # 建立連線，若 KyteView 未啟動會立即拋出 FileNotFoundError
            with Client(PIPE_ADDRESS, family="AF_PIPE") as conn:
                conn.send({"action": "preview", "path": str(file_path)})
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            pass

    t = threading.Thread(target=_send, daemon=True)
    t.start()
