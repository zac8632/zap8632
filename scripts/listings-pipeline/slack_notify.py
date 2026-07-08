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


def notify(text, blocks=None, webhook=None):
    """Post to Slack. `text` is the plain fallback (used for the mobile
    notification preview and accessibility); `blocks` is an optional Block
    Kit list for a nicely-formatted in-channel message."""
    webhook = webhook or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print("[slack] SLACK_WEBHOOK_URL not set - skipping notification.",
              file=sys.stderr)
        return False
    body = {"text": text}
    if blocks:
        body["blocks"] = blocks
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True
    except Exception as e:  # noqa: BLE001 - never let a ping break the job
        print(f"[slack] notification failed: {e}", file=sys.stderr)
        return False


def header(text):
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": True}}


def section(mrkdwn):
    return {"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn}}


def fields(pairs):
    """A 2-column stat grid. pairs = [(label, value), ...]."""
    return {"type": "section",
            "fields": [{"type": "mrkdwn", "text": f"*{k}*\n{v}"} for k, v in pairs]}


def context(mrkdwn):
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": mrkdwn}]}


DIVIDER = {"type": "divider"}


if __name__ == "__main__":
    ok = notify(" ".join(sys.argv[1:]) or "(empty message)")
    sys.exit(0)  # always exit 0 - notifications are best-effort
