"""Extract the cloudflare tunnel URL from a running tunnel."""
import subprocess
import sys
import re
import time

proc = subprocess.Popen(
    ['.\\cloudflared.exe', 'tunnel', '--url', 'http://localhost:8080'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

start = time.time()
url_found = False

for line in proc.stdout:
    line = line.strip()
    if line:
        print(line, flush=True)
    
    # Look for the trycloudflare URL
    match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
    if match:
        url = match.group(1)
        print(f"\n{'='*60}", flush=True)
        print(f"PUBLIC URL: {url}", flush=True)
        print(f"DASHBOARD: {url}/dashboard", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        # Write URL to file for easy access
        with open("PUBLIC_URL.txt", "w") as f:
            f.write(f"Public URL: {url}\n")
            f.write(f"Dashboard: {url}/dashboard\n")
            f.write(f"API Docs: {url}/docs\n")
        
        url_found = True
    
    # Timeout after 30s if no URL found
    if time.time() - start > 30 and not url_found:
        print("Timeout waiting for URL", flush=True)
        break

# Keep the tunnel alive
if url_found:
    print("Tunnel is running. Press Ctrl+C to stop.", flush=True)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
