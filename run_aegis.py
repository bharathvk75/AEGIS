#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import time
import signal

# Text color formatting helper
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_log(prefix, line, color):
    if line.strip():
        print(f"{color}{prefix} |{Colors.ENDC} {line.strip()}")

def log_reader(process, prefix, color):
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        print_log(prefix, line, color)

def check_python_environment():
    print(f"{Colors.HEADER}{Colors.BOLD}[AEGIS] Checking Python Environment...{Colors.ENDC}")
    
    # Check if we are running in venv
    venv_python = os.path.join("venv", "Scripts", "python.exe")
    if os.name != 'nt':
         venv_python = os.path.join("venv", "bin", "python")
         
    python_exe = sys.executable
    if os.path.exists(venv_python):
        python_exe = venv_python
        print(f"{Colors.GREEN}[AEGIS] Found local virtual environment Python: {python_exe}{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}[AEGIS] Virtual environment python not found at {venv_python}. Using system python.{Colors.ENDC}")
        
    # Check dependencies via uv
    try:
        print(f"{Colors.BLUE}[AEGIS] Verifying backend dependencies using uv...{Colors.ENDC}")
        subprocess.run(["uv", "pip", "install", "fastapi", "uvicorn", "--python", python_exe], check=True)
        print(f"{Colors.GREEN}[AEGIS] Backend dependencies verified.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}[AEGIS] Failed to run uv pip install. Attempting standard pip...{Colors.ENDC}")
        try:
            subprocess.run([python_exe, "-m", "pip", "install", "fastapi", "uvicorn"], check=True)
            print(f"{Colors.GREEN}[AEGIS] Backend dependencies verified via pip.{Colors.ENDC}")
        except Exception as e2:
            print(f"{Colors.FAIL}[AEGIS] Failed to install backend dependencies: {e2}{Colors.ENDC}")
            sys.exit(1)
            
    return python_exe

def check_node_environment():
    print(f"\n{Colors.HEADER}{Colors.BOLD}[AEGIS] Checking Node.js Environment...{Colors.ENDC}")
    
    # Check node and npm
    try:
        node_ver = subprocess.run(["node", "-v"], capture_output=True, text=True, check=True)
        print(f"{Colors.GREEN}[AEGIS] Found Node.js: {node_ver.stdout.strip()}{Colors.ENDC}")
    except Exception:
        print(f"{Colors.FAIL}[AEGIS] Node.js not found! Please install Node.js (v18+) to run the web frontend.{Colors.ENDC}")
        sys.exit(1)
        
    # Check if node_modules exists in frontend/
    node_modules = os.path.join("frontend", "node_modules")
    if not os.path.exists(node_modules):
        print(f"{Colors.WARNING}[AEGIS] frontend/node_modules not found. Running npm install...{Colors.ENDC}")
        try:
            subprocess.run(["npm", "install"], cwd="frontend", shell=True, check=True)
            print(f"{Colors.GREEN}[AEGIS] Frontend node modules installed.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}[AEGIS] Failed to run npm install: {e}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.GREEN}[AEGIS] Frontend node modules already installed.{Colors.ENDC}")

def main():
    # Print cool banner
    print(f"""{Colors.BLUE}{Colors.BOLD}
      █████╗ ███████╗ ██████╗ ██╗███████╗
     ██╔══██╗██╔════╝██╔════╝ ██║██╔════╝
     ███████║█████╗  ██║  ███╗██║███████╗
     ██╔══██║██╔══╝  ██║   ██║██║╚════██║
     ██║  ██║███████╗╚██████╔╝██║███████║
     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝
        Edge Video Analytics Redesign
    {Colors.ENDC}""")
    
    python_exe = check_python_environment()
    check_node_environment()
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}[AEGIS] Launching Services Concurrently...{Colors.ENDC}")
    print(f"{Colors.BLUE}Press Ctrl+C to terminate both servers at any time.{Colors.ENDC}\n")
    
    # Start Backend FastAPI
    print(f"{Colors.GREEN}[AEGIS] Starting FastAPI backend on http://localhost:8000...{Colors.ENDC}")
    backend_proc = subprocess.Popen(
        [python_exe, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Start Frontend Vite
    print(f"{Colors.GREEN}[AEGIS] Starting React dev server on http://localhost:5173...{Colors.ENDC}")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True,
        bufsize=1
    )
    
    # Create threads to read and print output
    backend_thread = threading.Thread(
        target=log_reader, 
        args=(backend_proc, "API-Backend", Colors.GREEN),
        daemon=True
    )
    frontend_thread = threading.Thread(
        target=log_reader, 
        args=(frontend_proc, "Web-Frontend", Colors.BLUE),
        daemon=True
    )
    
    backend_thread.start()
    frontend_thread.start()
    
    # Automatically open web browser after a brief delay for servers to bind
    def open_browser():
        time.sleep(2.0)
        import webbrowser
        print(f"{Colors.HEADER}{Colors.BOLD}[AEGIS] Opening browser at http://localhost:5173...{Colors.ENDC}")
        webbrowser.open("http://localhost:5173")
        
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Handle graceful exit
    def signal_handler(sig, frame):
        print(f"\n{Colors.WARNING}[AEGIS] Shutting down services...{Colors.ENDC}")
        
        # Terminate processes
        try:
            backend_proc.terminate()
            print(f"{Colors.GREEN}[AEGIS] Backend service terminated.{Colors.ENDC}")
        except Exception:
            pass
            
        try:
            # On Windows, we need taskkill or similar to kill node subprocesses properly
            if os.name == 'nt':
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_proc.pid)], capture_output=True)
            else:
                frontend_proc.terminate()
            print(f"{Colors.BLUE}[AEGIS] Frontend service terminated.{Colors.ENDC}")
        except Exception:
            pass
            
        print(f"{Colors.HEADER}{Colors.BOLD}[AEGIS] All services stopped. Goodbye!{Colors.ENDC}")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep main thread alive
    while True:
        try:
            time.sleep(1)
            # Check if any process died
            if backend_proc.poll() is not None:
                print(f"{Colors.FAIL}[AEGIS] Backend process exited unexpectedly with code {backend_proc.returncode}.{Colors.ENDC}")
                signal_handler(None, None)
            if frontend_proc.poll() is not None:
                print(f"{Colors.FAIL}[AEGIS] Frontend process exited unexpectedly with code {frontend_proc.returncode}.{Colors.ENDC}")
                signal_handler(None, None)
        except KeyboardInterrupt:
            signal_handler(None, None)

if __name__ == "__main__":
    main()
