import socket
import subprocess
import datetime
import os
import urllib.request
import io 
from contextlib import redirect_stdout
def get_hostname():
    hostname = socket.gethostname()
    return hostname

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("8.8.8.8", 80))
            return connection.getsockname()[0]
    except OSError:
        return "UNavailable"

def get_default_gateway():
    result = subprocess.run(
        ["route", "-n", "get", "default"],
        capture_output=True,
        text=True
    )
    
    for line in result.stdout.splitlines():
        if "gateway:" in line:
           return line.split()[1]

    return "Not found"

def ping_host(host):
    if host in ("Not found", "Unavailable"):
        return "SKIPPED - No valid destination"

    try:
        result = subprocess.run(
            ["ping", "-c", "4", "-W", "1000", host],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            return "PASS"
        else:
            return "FAIL"

    except (OSError, subprocess.TimeoutExpired):
        return "FAIL - Unable to complete test"

def test_dns(domain):
    try:
        ip = socket.gethostbyname(domain)
        return f"PASS - {ip}"
    except socket.gaierror: 
        return "FAIL"

def network_performance(host):
    try:
        result = subprocess.run(
            ["ping", "-c", "5", "-W", "1000", host],
            capture_output=True,
            text=True,
            timeout=15
        )

        found = False

        for line in result.stdout.splitlines():
            if "packet loss" in line or "min/avg/max" in line:
                print(line)
                found = True

        if not found:
            print("Performance data unavailable")

    except (OSError, subprocess.TimeoutExpired):
        print("Performance test failed")

def test_https(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return f"PASS - HTTP {response.status}"
    except Exception:
        return "FAIL"

def assess_network(local_ip, gateway, external, dns, https):
    if local_ip == "Unavailable":
        return "OFFLINE - No usable IPv4 route detected"

    if https.startswith("PASS"):
        if gateway == "FAIL":
            return "ONLINE - Gateway not responding to ICMP"
        return "ONLINE - Web connectivity operational"

    if external == "PASS" and dns == "FAIL":
        return "DEGRADED - Possible DNS issue"

    if external == "FAIL" and gateway == "PASS":
        return "DEGRADED - Possible upstream connectivity issue"

    return "INCONCLUSIVE - Further investigation required"

def run_diagnostics():
    print("=" * 45)
    print("NETWORK HEALTH MONITOR")
    print(datetime.datetime.now().astimezone().isoformat())
    print("=" * 45)

    local_ip = get_local_ip()
    gateway_ip = get_default_gateway()
    gateway = ping_host(gateway_ip)
    external = ping_host("8.8.8.8")
    dns = test_dns("google.com")
    https = test_https("https://www.google.com")

    print("Hostname:", get_hostname())
    print("Local IPv4:", local_ip)
    print("Default Gateway:", gateway_ip)
    print("Gateway ICMP Response:", gateway)
    print("External Connectivity:", external)
    print("DNS Resolution:", dns)

    print("\nNetwork Performance:")
    network_performance("8.8.8.8")

    print("HTTPS Connectivity:", https)

    print("\nDiagnostic Assessment:")
    print(assess_network(local_ip, gateway, external, dns, https))

    print("=" * 45)

log_directory = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs"
)

os.makedirs(log_directory, exist_ok=True)

buffer = io.StringIO()

with redirect_stdout(buffer):
    run_diagnostics()

report = buffer.getvalue()

print(report)

log_file = os.path.join(log_directory, "network_report.txt")

with open(log_file, "a") as file:
    file.write(report + "\n")

print("Diagnostic report saved:", log_file)
