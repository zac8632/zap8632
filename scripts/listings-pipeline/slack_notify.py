#!/usr/bin/env python3
"""
Tiny Slack notifier used by the pipeline workflows to ping a channel when an
automation finishes. Posts to an Incoming Webhook whose URL is read from the
SLACK_WEBHOOK_URL environment variable (set from the repo secret of the same
name in the workflows).

Deliberately fail-soft: if the webhook isn't configured, or Slack is briefly
unreachable, it logs to stderr and returns False rather than raising - a
missing notification must never fail the actual scrape/build job.

    from slack_notify import notify
    notify("Daily scrape done: 4,521 listings")

or standalone:
    python slack_notify.py "some message"
"""

import json
import os
import sys
import urllib.request


def notify(text, webhook=None):
    webhook = webhook or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print("[slack] SLACK_WEBHOOK_URL not set - skipping notification.",
              file=sys.stderr)
        return False
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True
    except Exception as e:  # noqa: BLE001 - never let a ping break the job
        print(f"[slack] notification failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    ok = notify(" ".join(sys.argv[1:]) or "(empty message)")
    sys.exit(0 if ok else 0)  # always exit 0 - notifications are best-effort
