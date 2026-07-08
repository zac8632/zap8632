#!/usr/bin/env python3
"""
Telegram-bot ingestion for the listing-content-studio pipeline (non-mudah
source). A colleague forwards a WhatsApp listing (free-text description +
photos) into a Telegram chat with our bot; this script polls Telegram's Bot
API for new messages, groups them into per-listing batches, extracts
whatever structured fields it can from the free text (same "omit if unknown"
rule as the scraper - never invents a field), downloads the photos at full
original Telegram quality (no watermark, no CDN compression - this is the
whole point of this second source), and feeds the result through the SAME
photo_curate.py + post_content.py pipeline used for mudah listings.

Requires a Telegram bot token (from @BotFather) as env var
TELEGRAM_BOT_TOKEN. Restricts processing to chat IDs in ALLOWED_CHAT_IDS so
random senders can't inject listings - empty means reject everyone (safe
default) until configured; the log tells you the chat_id to whitelist the
first time your colleague messages the bot.

Usage:
    python telegram_listings.py --out telegram_input --state telegram_input/telegram_state.json
    python telegram_listings.py --dry-run          # fetch + parse only, no photo download/render
    python telegram_listings.py --force-flush      # process pending batches now (manual testing)
"""

import argparse
import json
import os
import re
import sys
import time

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

# Chat IDs allowed to submit listings via the bot. Empty = reject everyone.
# Find your chat_id by messaging @userinfobot on Telegram, or from this
# script's own log output the first time an unrecognised chat_id messages it.
ALLOWED_CHAT_IDS = {312587269}

# How long to wait after the last message in a chat before treating the
# batch as "complete" and processing it - colleague may send photos then
# caption, or vice versa, across several messages in quick succession.
BATCH_IDLE_SECONDS = 10 * 60

PENANG_AREAS = [
    "George Town", "Georgetown", "Air Itam", "Ayer Itam", "Bayan Baru",
    "Bayan Lepas", "Batu Ferringhi", "Tanjung Bungah", "Tanjong Bungah",
    "Gelugor", "Jelutong", "Pulau Tikus", "Sungai Ara", "Sungai Nibong",
    "Relau", "Bukit Jambul", "Green Lane", "Farlim", "Paya Terubong",
    "Tanjung Tokong", "Tanjong Tokong", "Batu Uban", "Sungai Dua",
    "Bukit Gambier", "Balik Pulau", "Teluk Bahang", "Island Glades",
    "Gurney", "Seri Tanjung Pinang", "Andaman", "Quayside",
]

PRICE_RE = re.compile(r"RM\s?([\d,]+(?:\.\d+)?)\s*(mil|million|k)?\b", re.IGNORECASE)
# Bare "3.5mil"/"3.5 million" without an "RM" prefix - deliberately does NOT
# accept a bare lone "m"/"k" here (too ambiguous, e.g. "3m from LRT" is a distance).
PRICE_BARE_RE = re.compile(r"\b([\d.]+)\s*(mil|million)\b", re.IGNORECASE)
# Both orders seen in real listings: "3+1 bedrooms" AND the reversed label
# style "Bedroom：5" (colon, incl. full-width "：" from some templates).
# [ \t]* (not \s*) between the number and the keyword - deliberately does NOT
# cross a newline, or e.g. "Built-Up ...: 2899\nBedroom：5" would misparse the
# 2899 as the bed count (whitespace incl. \n would otherwise bridge the lines).
BED_RE = re.compile(r"(\d+(?:[ \t]*\+[ \t]*\d+)?)[ \t]*(?:bed(?:room)?s?|br)\b", re.IGNORECASE)
BED_LABEL_RE = re.compile(r"bedroom\s*[:：]\s*(\d+(?:[ \t]*\+[ \t]*\d+)?)", re.IGNORECASE)
BATH_RE = re.compile(r"(\d+(?:[ \t]*\+[ \t]*\d+)?)[ \t]*(?:bath(?:room)?s?|ba)\b", re.IGNORECASE)
BATH_LABEL_RE = re.compile(r"bathroom\s*[:：]\s*(\d+(?:[ \t]*\+[ \t]*\d+)?)", re.IGNORECASE)
# Bare "3,450sf" style (assumed built-up) and explicit labeled fields.
SIZE_RE = re.compile(r"([\d,]+)\s*(?:sq\.?\s?ft|sf|sqft)\b", re.IGNORECASE)
BUILTUP_LABEL_RE = re.compile(r"built[-\s]?up\s*(?:\(sq\.?\s?ft\))?\s*[:：]?\s*([\d,]+)", re.IGNORECASE)
LANDAREA_LABEL_RE = re.compile(r"land\s*(?:area|size)\s*(?:\(sq\.?\s?ft\))?\s*[:：]?\s*([\d,]+)", re.IGNORECASE)
TENURE_RE = re.compile(r"\b(freehold|leasehold)\b", re.IGNORECASE)
FURNISHING_RE = re.compile(r"furnish(?:ed|ing)?\s*[:：]\s*([A-Za-z]+)", re.IGNORECASE)
FACING_RE = re.compile(r"facing\s*[:：]\s*([A-Za-z]+)", re.IGNORECASE)
RENT_RE = re.compile(r"\b(for rent|to let|rental)\b", re.IGNORECASE)
# Sent by the user once they're done forwarding photos/text for one listing -
# finalizes that chat's batch immediately instead of waiting for the idle
# timer. Matches on its own line/message so it can't accidentally trigger
# mid-sentence in a real listing description.
CONFIRM_RE = re.compile(r"^\s*(done|confirm|confirmed|ready|go|✅|👍)\s*[.!]?\s*$", re.IGNORECASE)
# Sent to explicitly discard whatever's buffered so far before starting a new
# listing - the safety valve for "forgot to send 'done' before pasting the
# next one", since batching otherwise has no way to know a new listing has
# started (see poll_and_buffer()).
RESET_RE = re.compile(r"^\s*(new|reset|start over|clear|cancel)\s*[.!]?\s*$", re.IGNORECASE)
# Generic banner lines ("FOR SALE!!", "HOT LISTING") that aren't useful as a
# Title - skip these when picking the first line, they carry no project info.
BANNER_LINE_RE = re.compile(
    r"^[\s\W]*(for sale|for rent|new listing|hot listing|just listed|"
    r"must view|good deal|fast sale|urgent sale)[\s\W]*$", re.IGNORECASE)
# A template label with nothing after it yet ("Property Address :") - not
# useful as a Title either; the real value is usually on the next line.
LABEL_ONLY_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z\s]*[:：]\s*$")
# The agent's own name/phone line - stripped out entirely (never reaches
# Description/captions/creatives) and kept ONLY in a private internal field
# for the user's own reference, per their explicit instruction.
AGENT_LINE_RE = re.compile(r"^\s*(?:listing\s*agent|agent)\s*[:：]\s*(.+)$",
                           re.IGNORECASE | re.MULTILINE)

LANDED_KEYWORDS = ["terrace", "semi-d", "semi d", "bungalow", "link house",
                   "townhouse", "double storey", "single storey", "storey", "villa"]
COMMERCIAL_KEYWORDS = ["shop", "office", "retail", "commercial", "shoplot"]
LAND_KEYWORDS = ["land for sale", "vacant land", "plot of land"]


def _clean_text(t):
    return re.sub(r"\s+", " ", (t or "")).strip()


def extract_agent_and_strip(raw_text):
    """Pulls out an 'Agent: Name 012-xxx' style line for PRIVATE reference
    only, and returns the text with that line removed so it never reaches
    Description, captions, or any public-facing field."""
    m = AGENT_LINE_RE.search(raw_text)
    if not m:
        return None, raw_text
    agent_contact = m.group(1).strip()
    stripped = AGENT_LINE_RE.sub("", raw_text).strip()
    return agent_contact, stripped


def extract_price(text):
    """Returns a float RM amount, or None. Every value traces to a number the
    colleague actually typed - "3.5mil"/"998 K" style shorthand is expanded, a
    bare "RM 380,000" is used as-is, nothing is guessed beyond unit conversion."""
    m = PRICE_RE.search(text)
    if m:
        num = float(m.group(1).replace(",", ""))
        suffix = (m.group(2) or "").lower()
        if suffix in ("mil", "million"):
            num *= 1_000_000
        elif suffix == "k":
            num *= 1_000
        elif num < 1000:
            # "RM 3.5" with no explicit unit almost always means RM 3.5 million
            # shorthand in this market - full numbers are never typed this way.
            num *= 1_000_000
        return num
    m2 = PRICE_BARE_RE.search(text)
    if m2:
        return float(m2.group(1)) * 1_000_000
    return None


def extract_sizes(text):
    """Returns (built_up_sqft, land_sqft) as strings, either may be None.
    Prefers explicit 'Built-Up (sqft): N' / 'Land Area (sqft): N' labels;
    falls back to a bare 'N sf'/'N sqft' as built-up if no label present."""
    built_up = land = None
    m = BUILTUP_LABEL_RE.search(text)
    if m:
        built_up = m.group(1).replace(",", "")
    m = LANDAREA_LABEL_RE.search(text)
    if m:
        land = m.group(1).replace(",", "")
    if built_up is None:
        m = SIZE_RE.search(text)
        if m:
            built_up = m.group(1).replace(",", "")
    return built_up, land


def extract_area(text):
    low = text.lower()
    for area in PENANG_AREAS:
        if area.lower() in low:
            return area
    return None


def extract_asset_type_and_property_type(text):
    low = text.lower()
    if any(k in low for k in LAND_KEYWORDS):
        return "land", "Land"
    if any(k in low for k in COMMERCIAL_KEYWORDS):
        return "commercial", "Commercial Property"
    if any(k in low for k in LANDED_KEYWORDS):
        return "residential", "Landed House"
    if "condo" in low or "apartment" in low or "service residence" in low or "studio" in low:
        return "residential", "Condominium"
    return "residential", None  # can't tell - leave Property Type blank


def parse_listing_text(raw_text):
    """Best-effort structured extraction from a free-text listing description.
    Every field traces directly to text in the message; unclear fields are
    left as None (never guessed) per the no-hallucination rule."""
    raw_text = raw_text or ""

    # Strip the agent name/phone line FIRST - it must never reach Description,
    # Title, or any field a caption/creative could draw from. Kept separately
    # in a private "_agent_contact_internal" field for the user's own records.
    agent_contact, text = extract_agent_and_strip(raw_text)

    # Title = the first substantive line, extracted BEFORE collapsing
    # newlines (regex fields below tolerate embedded newlines fine, so
    # extraction runs against the agent-stripped text - only Description gets
    # flattened to one line).
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    substantive = [l for l in lines
                   if not BANNER_LINE_RE.match(l) and not LABEL_ONLY_LINE_RE.match(l)]
    title = (substantive or lines or [None])[0]

    price = extract_price(text)
    area = extract_area(text)
    bed_m = BED_RE.search(text) or BED_LABEL_RE.search(text)
    bath_m = BATH_RE.search(text) or BATH_LABEL_RE.search(text)
    built_up, land = extract_sizes(text)
    tenure_m = TENURE_RE.search(text)
    furnishing_m = FURNISHING_RE.search(text)
    facing_m = FACING_RE.search(text)
    asset_type, property_type = extract_asset_type_and_property_type(text)
    action = "For Rent" if RENT_RE.search(text) else "For Sale"

    return {
        "Title": title,
        "Description": _clean_text(text),
        "Location": area,
        "Price (RM)": price,
        "Price": f"RM {int(price):,}" if price else None,
        "Bedrooms": re.sub(r"[ \t]*\+[ \t]*", "+", bed_m.group(1)) if bed_m else None,
        "Bathrooms": re.sub(r"[ \t]*\+[ \t]*", "+", bath_m.group(1)) if bath_m else None,
        "Size (sqft)": built_up,
        "Land Size": land,
        "Tenure": tenure_m.group(1).title() if tenure_m else None,
        "Furnishing": furnishing_m.group(1).title() if furnishing_m else None,
        "Facing": facing_m.group(1).title() if facing_m else None,
        "Asset Type": asset_type,
        "Property Type": property_type,
        "Category": f"{property_type or 'Property'} {action}",
        "_agent_contact_internal": agent_contact,  # PRIVATE - never public
    }


def tg_call(token, method, params=None, timeout=30):
    r = requests.get(TELEGRAM_API.format(token=token, method=method), params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]


def tg_send_message(token, chat_id, text):
    """Best-effort reply back to the user - a failed send should never break
    ingestion, just gets logged."""
    try:
        tg_call(token, "sendMessage", {"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"  [telegram] failed to send confirmation message: {e}", file=sys.stderr)


def tg_send_media_group(token, chat_id, photo_paths, caption=None):
    """Send up to 10 photos as a single Telegram album - the caption (if
    given) shows under the first photo. Lets the user save/forward the
    finished creatives straight from the chat, no zip download needed."""
    photo_paths = photo_paths[:10]
    if not photo_paths:
        return
    media = []
    files = {}
    for i, path in enumerate(photo_paths):
        key = f"photo{i}"
        entry = {"type": "photo", "media": f"attach://{key}"}
        if i == 0 and caption:
            entry["caption"] = caption
        media.append(entry)
        files[key] = open(path, "rb")
    try:
        r = requests.post(
            TELEGRAM_API.format(token=token, method="sendMediaGroup"),
            data={"chat_id": chat_id, "media": json.dumps(media)},
            files=files, timeout=60)
        r.raise_for_status()
        if not r.json().get("ok"):
            print(f"  [telegram] sendMediaGroup failed: {r.json()}", file=sys.stderr)
    except Exception as e:
        print(f"  [telegram] failed to send media group: {e}", file=sys.stderr)
    finally:
        for f in files.values():
            f.close()


def download_telegram_file(token, file_id, out_path):
    file_info = tg_call(token, "getFile", {"file_id": file_id})
    file_path = file_info["file_path"]
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)


def load_state(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_update_id": 0, "pending": {}}


def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def fetch_new_updates(token, offset):
    return tg_call(token, "getUpdates", {"offset": offset, "timeout": 0})


def poll_and_buffer(token, state):
    """Fetch new Telegram messages since the last saved offset and buffer
    them per chat. Does not process/finalize anything yet - see
    process_batches()."""
    offset = state.get("last_update_id", 0)
    updates = fetch_new_updates(token, offset)
    pending = state.setdefault("pending", {})

    for upd in updates:
        state["last_update_id"] = upd["update_id"] + 1
        msg = upd.get("message") or upd.get("channel_post")
        if not msg:
            continue
        chat_id = str(msg["chat"]["id"])

        if not ALLOWED_CHAT_IDS:
            print(f"  [telegram] ALLOWED_CHAT_IDS is empty - rejecting all senders. "
                  f"This message was from chat_id={chat_id} - whitelist it in "
                  f"telegram_listings.py to allow your colleague's chat.", file=sys.stderr)
            continue
        if int(chat_id) not in ALLOWED_CHAT_IDS:
            print(f"  [telegram] ignoring message from unauthorised chat_id={chat_id}", file=sys.stderr)
            continue

        # Key batches by (chat, sender), not just chat - so if this bot ever
        # ends up in a group instead of 1:1, two different people's
        # submissions in the same chat never merge into one batch.
        sender_id = str((msg.get("from") or {}).get("id", "0"))
        batch_key = f"{chat_id}:{sender_id}"

        text = msg.get("text") or msg.get("caption")
        if text and RESET_RE.match(text):
            if batch_key in pending:
                del pending[batch_key]
                tg_send_message(token, chat_id, "Cleared - send the next listing whenever you're ready.")
            continue

        batch = pending.setdefault(batch_key, {
            "chat_id": chat_id, "first_msg_time": time.time(), "last_msg_time": time.time(),
            "texts": [], "photo_file_ids": [], "confirmed": False,
        })

        if text and CONFIRM_RE.match(text) and (batch["texts"] or batch["photo_file_ids"]):
            # A confirm signal on an EMPTY batch is just noise (nothing to
            # confirm yet) - only finalize a batch that actually has content.
            batch["confirmed"] = True
            tg_send_message(
                token, chat_id,
                f"Got it - {len(batch['photo_file_ids'])} photo(s) and "
                f"{len(batch['texts'])} text message(s) received. Processing "
                f"this listing now, no need to send anything else for it.")
        else:
            got_photo = bool(msg.get("photo"))
            if text:
                batch["texts"].append(text)
            if got_photo:
                largest = max(msg["photo"], key=lambda p: p["width"])
                batch["photo_file_ids"].append(largest["file_id"])
            if text or got_photo:
                # Acknowledge every message so the user always knows it was
                # received and can see the running tally, instead of sending
                # things into silence until the whole batch finalizes.
                what = "photo" if got_photo else "text"
                tg_send_message(
                    token, chat_id,
                    f"Got your {what} ({len(batch['photo_file_ids'])} photo(s), "
                    f"{len(batch['texts'])} text message(s) so far). Send more, "
                    f"or type 'done' when finished.")
        batch["last_msg_time"] = time.time()

    return state


def process_batches(token, state, out_dir, dry_run=False):
    """Flush any chat's buffered batch once idle long enough (or always, if
    the caller already forced idle via --force-flush). Returns finalized
    listing dicts (with a 'photos' path list) ready for the curation +
    creative pipeline."""
    pending = state.setdefault("pending", {})
    now = time.time()
    finalized = []

    for batch_key, batch in list(pending.items()):
        if not batch.get("confirmed") and now - batch["last_msg_time"] <= BATCH_IDLE_SECONDS:
            continue

        chat_id = batch["chat_id"]
        if not batch.get("confirmed") and not dry_run:
            # Timed out idle rather than an explicit "done" - the confirmed
            # path already told the user processing started, so only notify
            # here for the silent-timeout path (otherwise they'd never know
            # the bot picked it up without watching the workflow run).
            tg_send_message(
                token, chat_id,
                f"No activity for a while - processing your listing now "
                f"({len(batch['photo_file_ids'])} photo(s), "
                f"{len(batch['texts'])} text message(s)).")
        text = "\n".join(batch["texts"])
        if text:
            listing = parse_listing_text(text)
        else:
            listing = {
                "Title": None, "Description": None, "Location": None,
                "Price (RM)": None, "Price": None, "Bedrooms": None,
                "Bathrooms": None, "Size (sqft)": None, "Tenure": None,
                "Asset Type": "residential", "Property Type": None,
                "Category": "Property For Sale",
            }
        listing["_chat_id"] = chat_id
        listing["_batch_id"] = f"{batch_key.replace(':', '_')}_{int(batch['first_msg_time'])}"
        listing_dir = os.path.join(out_dir, listing["_batch_id"])
        photos_dir = os.path.join(listing_dir, "photos")
        os.makedirs(photos_dir, exist_ok=True)

        saved = []
        if not dry_run:
            for i, file_id in enumerate(batch["photo_file_ids"], 1):
                fn = os.path.join(photos_dir, f"{i:02d}.jpg")
                try:
                    download_telegram_file(token, file_id, fn)
                    saved.append(fn)
                except Exception as e:
                    print(f"  [telegram] photo download failed: {e}", file=sys.stderr)
        listing["photos"] = saved
        # This repo is PUBLIC - listing_raw.json ends up in a workflow
        # artifact (publicly downloadable on a public repo's Actions tab).
        # Never write the private agent field here; it goes ONLY into the
        # Excel log (see append_to_excel_log / main()) - and even that has
        # the same public-repo exposure risk, flagged separately.
        with open(os.path.join(listing_dir, "listing_raw.json"), "w") as f:
            json.dump({k: v for k, v in listing.items()
                       if k not in ("photos", "_agent_contact_internal")}, f, indent=2)

        if listing["Title"] or saved:
            finalized.append(listing)
        del pending[batch_key]

    return finalized


# Personal reference log - EVERY listing submitted via Telegram gets a row
# here, including the agent name/contact, for the user's own future
# reference.
#
# IMPORTANT: this repo is PUBLIC, so this data must never land in a git
# commit (a "data branch" is just a public branch) or a workflow artifact
# (also publicly downloadable on a public repo, no login required). The real
# destination is a PRIVATE Google Sheet via sync_agent_log_to_gsheet() below,
# reusing the same service-account secret (GSHEET_SERVICE_ACCOUNT_JSON)
# already set up for the mudah pipeline - share a Sheet with that same
# service account's client_email and pass its ID as TELEGRAM_LOG_GSHEET_ID.
# append_to_excel_log() is kept only as a local/manual-testing helper - do
# NOT wire its output path into anything committed or uploaded.
LOG_COLUMNS = [
    "Processed At (UTC)", "Batch ID", "Chat ID", "Title", "Location",
    "Price", "Price (RM)", "Bedrooms", "Bathrooms", "Size (sqft)",
    "Land Size", "Tenure", "Furnishing", "Facing", "Asset Type",
    "Property Type", "Category", "Agent Contact (private)", "Num Photos",
    "Description",
]


def sync_agent_log_to_gsheet(listing, gsheet_id, gsheet_key):
    """Append one row to a PRIVATE Google Sheet - the real destination for
    this data. Never touches git or any workflow artifact."""
    import datetime
    try:
        import gspread
    except ImportError:
        print("  [telegram] gspread not installed - skipping private log sync", file=sys.stderr)
        return
    try:
        gc = gspread.service_account(filename=gsheet_key)
        sh = gc.open_by_key(gsheet_id)
    except Exception as e:
        print(f"  [telegram] could not connect to private log Sheet: {e}", file=sys.stderr)
        return

    try:
        ws = sh.worksheet("Agent Log")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Agent Log", rows=1000, cols=len(LOG_COLUMNS) + 2)
        ws.append_row(LOG_COLUMNS, value_input_option="RAW")

    row = {
        "Processed At (UTC)": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "Batch ID": listing.get("_batch_id"),
        "Chat ID": listing.get("_chat_id"),
        "Agent Contact (private)": listing.get("_agent_contact_internal"),
        "Num Photos": len(listing.get("photos", [])),
    }
    for col in LOG_COLUMNS:
        if col not in row:
            row[col] = listing.get(col)
    values = [str(row.get(col) or "") for col in LOG_COLUMNS]
    try:
        # RAW (not USER_ENTERED) so a phone number never gets auto-parsed into
        # a number and loses its leading zero - same lesson as the mudah sync.
        ws.append_row(values, value_input_option="RAW")
        print(f"  [telegram] logged '{listing.get('Title')}' to private Sheet", file=sys.stderr)
    except Exception as e:
        print(f"  [telegram] failed to append to private Sheet: {e}", file=sys.stderr)


def append_to_excel_log(path, listing):
    import datetime
    import pandas as pd

    row = {
        "Processed At (UTC)": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "Batch ID": listing.get("_batch_id"),
        "Chat ID": listing.get("_chat_id"),
        "Agent Contact (private)": listing.get("_agent_contact_internal"),
        "Num Photos": len(listing.get("photos", [])),
    }
    for col in LOG_COLUMNS:
        if col not in row:
            row[col] = listing.get(col)

    new_row_df = pd.DataFrame([row], columns=LOG_COLUMNS)
    if os.path.exists(path):
        try:
            existing = pd.read_excel(path, dtype=str)
            existing = existing.reindex(columns=LOG_COLUMNS)
        except Exception as e:
            print(f"  [telegram] could not read existing log ({e}) - starting fresh", file=sys.stderr)
            existing = pd.DataFrame(columns=LOG_COLUMNS)
        combined = pd.concat([existing, new_row_df], ignore_index=True)
    else:
        combined = new_row_df
    combined.to_excel(path, index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="telegram_input")
    ap.add_argument("--state", default="telegram_input/telegram_state.json")
    ap.add_argument("--dry-run", action="store_true",
                     help="Fetch + parse only, skip photo download/rendering.")
    ap.add_argument("--force-flush", action="store_true",
                     help="Process all pending batches immediately, ignoring the idle timer "
                          "(useful for manual testing).")
    args = ap.parse_args()

    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN not set.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    state = load_state(args.state)
    state = poll_and_buffer(token, state)

    if args.force_flush:
        for batch in state.get("pending", {}).values():
            batch["last_msg_time"] = 0

    finalized = process_batches(token, state, args.out, dry_run=args.dry_run)
    save_state(args.state, state)

    print(f"{len(finalized)} listing(s) finalized this run.", file=sys.stderr)

    gsheet_id = os.environ.get("TELEGRAM_LOG_GSHEET_ID")
    gsheet_key = os.environ.get("TELEGRAM_LOG_GSHEET_KEY")
    if gsheet_id and gsheet_key:
        for listing in finalized:
            try:
                sync_agent_log_to_gsheet(listing, gsheet_id, gsheet_key)
            except Exception as e:
                print(f"  [telegram] failed to sync private log: {e}", file=sys.stderr)
    elif finalized:
        print("  [telegram] TELEGRAM_LOG_GSHEET_ID/KEY not set - skipping the "
              "private agent-contact log for this run (see context.md).", file=sys.stderr)

    if args.dry_run or not finalized:
        for listing in finalized:
            print(json.dumps({k: v for k, v in listing.items() if k != "photos"}, indent=2))
        return

    import photo_curate
    import post_content

    for listing in finalized:
        listing_dir = os.path.join(args.out, listing["_batch_id"])
        photos = listing.get("photos", [])
        if not photos:
            print(f"  [telegram] {listing['_batch_id']}: no photos, skipping render", file=sys.stderr)
            continue
        curated = photo_curate.select_representative_photos(photos, k=5)
        curated_paths = [c["path"] for c in curated] or photos[:5]
        creatives = post_content.render_creatives(
            curated_paths, listing, os.path.join(listing_dir, "creatives"))
        caps = post_content.build_captions(listing)
        with open(os.path.join(listing_dir, "captions.md"), "w") as f:
            for plat, txt in caps.items():
                f.write(f"## {plat}\n\n{txt}\n\n")
        print(f"  [ok] {listing['_batch_id']}: {len(curated_paths)} photos curated, "
              f"creatives + captions written", file=sys.stderr)

        # Send the finished creatives + every platform's caption straight back
        # into the chat - no artifact/zip download needed, just save/forward
        # the album and copy-paste whichever caption you're posting to.
        chat_id = listing["_chat_id"]
        feed_creatives = creatives.get("4x5", [])
        story_creatives = creatives.get("9x16", [])
        if feed_creatives:
            tg_send_media_group(
                token, chat_id, feed_creatives,
                caption=f"'{listing.get('Title') or listing['_batch_id']}' - "
                        f"{len(feed_creatives)} feed creative(s) (4:5, IG/Threads/TikTok)")
        if story_creatives:
            tg_send_media_group(
                token, chat_id, story_creatives,
                caption=f"{len(story_creatives)} vertical creative(s) (9:16, Story/Reels/TikTok)")
        if not feed_creatives and not story_creatives:
            tg_send_message(token, chat_id, "No creatives were rendered (no usable photos).")
        for plat, txt in caps.items():
            tg_send_message(token, chat_id, f"[{plat.upper()} CAPTION]\n\n{txt}")
        tg_send_message(
            token, chat_id,
            f"Done - '{listing.get('Title') or listing['_batch_id']}' is ready above. "
            f"It'll also show up in Airtable shortly.")

    # Best-effort Slack ping (no-op unless SLACK_WEBHOOK_URL is set).
    try:
        from slack_notify import notify
        titles = [listing.get("Title") or listing["_batch_id"] for listing in finalized]
        lines = [f"📩 *Telegram listing processed* — {len(titles)} finalized"]
        lines += [f"• {t}" for t in titles[:10]]
        notify("\n".join(lines))
    except Exception as e:  # noqa: BLE001 - notification is best-effort
        print(f"[slack] skipped: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
