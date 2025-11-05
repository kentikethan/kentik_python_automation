"""Enable flow and SNMP enrichment for all current NMS devices in Kentik.

This script:
- lists NMS devices from the Kentik API
- updates each device to enable flow and snmp enrichment

Usage:
  export KENTIK_API_BASE="https://api.kentik.com/api/v5"   # optional, defaults to above
  export KENTIK_API_TOKEN="..."                           # preferred: Bearer token
  python main.py [--dry-run]

Notes:
- The exact json keys used to enable enrichment may differ by Kentik API version.
  If updates fail, adjust the payload keys in `build_enrichment_payload`.
- Keep your API token private. Do not commit it to source control.
"""
import os
import sys
import time
import argparse
import requests

API_BASE = os.environ.get("KENTIK_API_BASE", "https://api.kentik.com/api/v5")
API_TOKEN = os.environ.get("KENTIK_API_TOKEN")  # preferred: Bearer token
REQUESTS_TIMEOUT = 30.0

# Add configurable defaults for planId and SNMP community
# Can be overridden via environment variables KENTIK_PLAN_ID and KENTIK_SNMP_COMMUNITY
DEFAULT_PLAN_ID = int(os.environ.get("KENTIK_PLAN_ID"))
DEFAULT_SNMP_COMMUNITY = os.environ.get("KENTIK_SNMP_COMMUNITY", "")

def auth_headers():
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    # fallback: allow user to provide basic auth via env for older setups
    user = os.environ.get("KENTIK_USER")
    key = os.environ.get("KENTIK_KEY")
    if user and key:
        # Some Kentik installations expect X-CH-Auth-Email and X-CH-Auth-API-Token or similar.
        return {"X-CH-Auth-User": user, "X-CH-Auth-Key": key, "Content-Type": "application/json"}
    raise SystemExit("No auth found. Set KENTIK_API_TOKEN or KENTIK_USER+KENTIK_KEY environment variables.")

def list_nms_devices():
    url = f"{API_BASE}/nms/devices"
    resp = requests.get(url, headers=auth_headers(), timeout=REQUESTS_TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def build_enrichment_payload(device):
    """
    Build payload in the requested 'device' object format.
    Uses DEFAULT_PLAN_ID and DEFAULT_SNMP_COMMUNITY when device does not contain those fields.
    """
    device_name = device.get("deviceName") or device.get("name") or device.get("hostname") or device.get("device_name") or device.get("id")
    sending_ips = device.get("sendingIps") or device.get("sendingIpsList") or device.get("deviceSnmpIp") or device.get("ip_address") or None
    site_id = device.get("siteId") or device.get("site_id") or None

    return {
        "device": {
            "deviceName": device_name,
            "deviceSubtype": "router",  # Default type, adjust if needed (e.g., "host", "switch")
            "sendingIps": sending_ips,
            "deviceSampleRate": 1,
            "deviceDescription": f"Device created by Kentik automation script: {device_name}",
            "deviceBgpType": "none",
            "planId": device.get("planId", DEFAULT_PLAN_ID),
            "minimize_snmp": False,
            "siteId": site_id,
            "deviceSnmpIp": device.get("deviceSnmpIp", sending_ips),
            "deviceSnmpCommunity": device.get("deviceSnmpCommunity", DEFAULT_SNMP_COMMUNITY)
        }
    }

def update_device(device_id, payload):
    url = f"{API_BASE}/nms/devices/{device_id}"
    # use PATCH if supported by your API; PUT can be used if required (and you must supply full object)
    resp = requests.patch(url, json=payload, headers=auth_headers(), timeout=REQUESTS_TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def main(dry_run=False, pause_between=0.1):
    print("Listing NMS devices...")
    data = list_nms_devices()
    # Response shape may wrap devices under a key like "devices" or be a plain list.
    devices = data.get("devices") if isinstance(data, dict) and "devices" in data else data
    if not devices:
        print("No devices returned by API.")
        return

    print(f"Found {len(devices)} devices. Preparing to enable enrichment on each device.")
    failures = []
    for d in devices:
        # device id field may be 'id' or 'device_id' depending on API version
        device_id = d.get("id") or d.get("device_id")
        name = d.get("name") or d.get("hostname") or device_id
        if not device_id:
            print(f"Skipping device without id: {name}")
            continue

        payload = build_enrichment_payload(d)
        print(f"{'DRY-RUN:' if dry_run else 'UPDATING:'} device {name} ({device_id}) -> {payload}")
        if dry_run:
            continue
        try:
            update_device(device_id, payload)
        except Exception as e:
            print(f"ERROR updating {device_id}: {e}")
            failures.append((device_id, str(e)))
        time.sleep(pause_between)

    if failures:
        print(f"Completed with {len(failures)} failures. See details:")
        for fid, reason in failures:
            print(f" - {fid}: {reason}")
    else:
        print("Completed successfully.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Only show changes, do not call API to update.")
    args = p.parse_args()
    try:
        main(dry_run=args.dry_run)
    except requests.HTTPError as he:
        print(f"HTTP error: {he} - response content: {getattr(he.response, 'text', '')}")
        sys.exit(2)
    except Exception as e:
        print(f"Fatal error: {e}")