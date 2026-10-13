import sys
import os
import time
import signal
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="AI Resume & Job Description Matcher Launcher")
    parser.add_argument("--backend-only", action="store_true", help="Start only the FastAPI backend")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the Streamlit frontend")
    parser.add_argument("--host", default="127.0.0.1", help="Backend host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=8501, help="Frontend port (default: 8501)")
    args = parser.parse_args()

    # Determine python executable
    python_exe = sys.executable

    processes = []

    def shutdown(sig=None, frame=None):
        print("\n[Launcher] Gracefully shutting down services...")
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("[Launcher] All processes terminated. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # 1. Start Backend
    if not args.frontend_only:
        print(f"[Launcher] Starting FastAPI backend on http://{args.host}:{args.port} ...")
        backend_cmd = [
            python_exe, "-m", "uvicorn", "backend.main:app",
            "--host", args.host,
            "--port", str(args.port),
            "--reload"
        ]
        p_backend = subprocess.Popen(backend_cmd)
        processes.append(p_backend)
        # Give backend a moment to start
        time.sleep(2)

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
        p_frontend = subprocess.Popen(frontend_cmd, env=env)
        processes.append(p_frontend)

    print("\n" + "="*60)
    print(" AI Resume & Job Description Matcher is Running!")
    print(f" • FastAPI Backend Docs:  http://{args.host}:{args.port}/docs")
    print(f" • FastAPI Health:        http://{args.host}:{args.port}/health")
    if not args.backend_only:
        print(f" • Streamlit Frontend:    http://localhost:{args.frontend_port}")
    print(" Press Ctrl+C at any time to stop all services.")
    print("="*60 + "\n")

    try:
        while True:
            # Check if any process died unexpectedly
            for p in processes:
                if p.poll() is not None:
                    print(f"[Launcher] Process {p.pid} exited with code {p.returncode}.")
                    shutdown()
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()
