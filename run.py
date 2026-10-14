import sys
import os
import time
import signal
import socket
import subprocess
import argparse
import urllib.request
import urllib.error

def is_port_in_use(host: str, port: int) -> bool:
    """Check if a port is already open/in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0

def check_health(url: str, timeout: float = 1.5) -> bool:
    """Check if backend /health endpoint responds with HTTP 200."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LauncherHealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False

def kill_process_tree(pid: int):
    """Terminate a process and all its descendants cleanly."""
    try:
        import psutil
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        parent.terminate()
        gone, alive = psutil.wait_procs(children + [parent], timeout=3)
        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="AI Resume & Job Description Matcher Launcher")
    parser.add_argument("--backend-only", action="store_true", help="Start only the FastAPI backend")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the Streamlit frontend")
    parser.add_argument("--host", default="127.0.0.1", help="Backend host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=8501, help="Frontend port (default: 8501)")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable
    processes = []

    def shutdown(sig=None, frame=None):
        print("\n[Launcher] Gracefully shutting down launcher services...")
        for p in processes:
            if p.poll() is None:
                kill_process_tree(p.pid)
        print("[Launcher] All launcher services terminated. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    health_url = f"http://{args.host}:{args.port}/health"

    # 1. Start Backend
    if not args.frontend_only:
        if is_port_in_use(args.host, args.port):
            if check_health(health_url, timeout=1.0):
                print(f"[Launcher] Notice: FastAPI backend is already running and healthy at http://{args.host}:{args.port}")
            else:
                print(f"[Launcher] ERROR: Port {args.port} is already in use on {args.host} by an unresponsive service.")
                print(f"[Launcher] Please free port {args.port} or run with --port <number>.")
                sys.exit(1)
        else:
            print(f"[Launcher] Starting FastAPI backend on http://{args.host}:{args.port} ...")
            backend_cmd = [
                python_exe, "-m", "uvicorn", "backend.main:app",
                "--host", args.host,
                "--port", str(args.port),
                "--reload"
            ]
            p_backend = subprocess.Popen(backend_cmd, cwd=project_root)
            processes.append(p_backend)

            # Health polling with timeout instead of arbitrary sleep
            print(f"[Launcher] Verifying FastAPI backend readiness at {health_url} ...")
            start_wait = time.time()
            max_wait_seconds = 20
            backend_ready = False

            while time.time() - start_wait < max_wait_seconds:
                if p_backend.poll() is not None:
                    print(f"[Launcher] ERROR: FastAPI process terminated unexpectedly with code {p_backend.returncode}.")
                    shutdown()
                    sys.exit(1)

                if check_health(health_url, timeout=1.0):
                    backend_ready = True
                    break
                time.sleep(0.5)

            if not backend_ready:
                print(f"[Launcher] ERROR: FastAPI backend failed to respond at {health_url} within {max_wait_seconds}s.")
                shutdown()
                sys.exit(1)

            print("[Launcher] FastAPI backend is ready and accepting requests.")

    # 2. Start Frontend
    if not args.backend_only:
        print(f"[Launcher] Starting Streamlit frontend on http://localhost:{args.frontend_port} ...")
        frontend_cmd = [
            python_exe, "-m", "streamlit", "run", "frontend/app.py",
            "--server.port", str(args.frontend_port),
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        env = os.environ.copy()
        env["BACKEND_URL"] = f"http://{args.host}:{args.port}"
        p_frontend = subprocess.Popen(frontend_cmd, env=env, cwd=project_root)
        processes.append(p_frontend)

    print("\n" + "="*60)
    print(" AI Resume & Job Description Matcher is Running!")
    print(f" • FastAPI Backend Docs:  http://{args.host}:{args.port}/docs")
    print(f" • FastAPI Health:        http://{args.host}:{args.port}/health")
    if not args.backend_only:
        print(f" • Streamlit Frontend:    http://localhost:{args.frontend_port}")
    print(" Press Ctrl+C at any time to stop all launcher services.")
    print("="*60 + "\n")

    try:
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"[Launcher] Child process {p.pid} exited with code {p.returncode}.")
                    shutdown()
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()

