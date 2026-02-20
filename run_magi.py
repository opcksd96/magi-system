import subprocess
import os
import signal
import sys
import time


def run_magi():
    # Paths
    root_dir = os.path.dirname(os.path.abspath(__file__))
    api_script = os.path.join(root_dir, "magi_api.py")
    ui_dir = os.path.join(root_dir, "magi-ui")

    # Determine python executable (assumes running from venv)
    python_exe = sys.executable

    print("\n--- MAGI SYSTEM UNIFIED STARTUP ---")
    print(f"[*] API: {api_script}")
    print(f"[*] UI:  {ui_dir}")
    print("------------------------------------\n")

    processes = []

    try:
        # Start API
        print("[+] Starting MAGI API...")
        api_proc = subprocess.Popen([python_exe, api_script], cwd=root_dir)
        processes.append(api_proc)

        # Start UI
        print("[+] Starting MAGI UI (Vite)...")
        # Use shell=True for npm on Windows
        ui_proc = subprocess.Popen(["npm", "run", "dev"], cwd=ui_dir, shell=True)
        processes.append(ui_proc)

        print("\n[!] MAGI SYSTEM IS DEPLOYED.")
        print("[!] Press Ctrl+C to terminate all systems.\n")

        # Keep the script running while children are alive
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"\n[!] Process {p.pid} terminated unexpectedly.")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n\n[-] TERMINATION SIGNAL RECEIVED. SHUTTING DOWN...")
        for p in processes:
            if p.poll() is None:
                print(f"[*] Terminating process {p.pid}...")
                # On Windows, taskkill might be cleaner for shell processes
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                        capture_output=True,
                    )
                else:
                    p.terminate()

        print("[!] ALL SYSTEMS OFFLINE. GOODBYE, SENPAI.")


if __name__ == "__main__":
    run_magi()
