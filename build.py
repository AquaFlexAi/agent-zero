import os
import sys
import subprocess
import argparse
import platform
import shutil

# Configuration
IMAGE_NAME = "flexia/agent-zero"
BASE_IMAGE = "agent0ai/agent-zero-base:latest"
DOCKERFILE = "DockerfileLocal"

def log(msg, level="INFO"):
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"
    }
    # On Windows, color codes might not work in standard cmd, but work in PowerShell/Terminal
    if platform.system() == "Windows":
        os.system('color') 
    
    print(f"{colors.get(level, '')}[{level}] {msg}{colors['RESET']}", flush=True)

def check_requirements():
    log("Checking build requirements...", "INFO")
    
    # 1. Check OS
    os_name = platform.system()
    log(f"Operating System: {os_name}", "INFO")
    
    # 2. Check Docker
    try:
        subprocess.check_call(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("Docker is installed and accessible.", "SUCCESS")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("Docker is NOT installed or not in PATH.", "ERROR")
        sys.exit(1)

    # 3. Check Dockerfile
    if not os.path.exists(DOCKERFILE):
        log(f"Dockerfile '{DOCKERFILE}' not found!", "ERROR")
        sys.exit(1)

    # 4. Security: Check .dockerignore
    if not os.path.exists(".dockerignore"):
        log("Security Warning: .dockerignore file missing! This is a security risk.", "WARNING")
        # Optional: Force creation?
        # with open(".dockerignore", "w") as f: f.write("knowledge/\nlogs/\n.env\n")
    else:
        log(".dockerignore found.", "SUCCESS")

def build_image(mode="prod", no_cache=False):
    log(f"Starting build for mode: {mode}", "INFO")
    
    tag = "latest" if mode == "prod" else "dev"
    full_image_name = f"{IMAGE_NAME}:{tag}"
    
    build_args = []
    if mode == "dev":
        # For dev mode, we definitely want local source. 
        # The DockerfileLocal logic requires BRANCH=local to use COPY'd files and skip git clone.
        build_args = ["--build-arg", "BRANCH=local"]
    else:
        # For prod, if we are building from local source using DockerfileLocal, we also need BRANCH=local.
        # If we wanted to build from upstream git, we wouldn't use DockerfileLocal (or we'd modify it).
        # Assuming user wants to build *this* source:
        build_args = ["--build-arg", "BRANCH=local"]
        
    cmd = [
        "docker", "build",
        "-f", DOCKERFILE,
        "-t", full_image_name
    ]
    
    if no_cache:
        cmd.append("--no-cache")
        
    cmd.extend(build_args)
    cmd.append(".")

    try:
        log(f"Executing: {' '.join(cmd)}", "INFO")
        subprocess.check_call(cmd)
        log(f"Build successful! Image: {full_image_name}", "SUCCESS")
    except subprocess.CalledProcessError as e:
        log(f"Build failed with exit code {e.returncode}", "ERROR")
        sys.exit(e.returncode)

def run_security_scan(image_name):
    # Basic scan using docker scan (if available) or trivy
    # Since we can't guarantee internal tools, we'll check for 'docker scan'
    # Actually, recent docker versions have 'docker scout' or 'docker scan' deprecated.
    # We will do a basic sanity check of image size and user.
    
    log("Running post-build security assertions...", "INFO")
    
    try:
        # Check Image Size
        out = subprocess.check_output(["docker", "inspect", "-f", "{{.Size}}", image_name]).decode().strip()
        size_mb = int(out) / (1024 * 1024)
        log(f"Image Size: {size_mb:.2f} MB", "INFO")
        if size_mb > 5000: # 5GB warning
            log("Warning: Image size is very large (>5GB).", "WARNING")

        # Check User (Mock check since we know it runs as root often in dev containers, but good to warn)
        user = subprocess.check_output(["docker", "inspect", "-f", "{{.Config.User}}", image_name]).decode().strip()
        if user == "" or user == "0" or user == "root":
            log("Security Warning: Container runs as ROOT. Recommended to use a non-root user.", "WARNING")
        else:
            log(f"Container runs as user: {user}", "SUCCESS")
            
    except Exception as e:
        log(f"Security check failed: {e}", "WARNING")

def main():
    parser = argparse.ArgumentParser(description="Build script for FlexIA Agent Zero")
    parser.add_argument("--mode", choices=["dev", "prod"], default="prod", help="Build mode")
    parser.add_argument("--no-cache", action="store_true", help="Disable build cache")
    
    args = parser.parse_args()
    
    check_requirements()
    build_image(args.mode, args.no_cache)
    
    tag = "latest" if args.mode == "prod" else "dev"
    run_security_scan(f"{IMAGE_NAME}:{tag}")

if __name__ == "__main__":
    main()
