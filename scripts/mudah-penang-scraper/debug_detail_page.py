#!/usr/bin/env python3
"""
One-off diagnostic: visits a single mudah.my listing detail page and
dumps everything that looks phone/contact-related to stdout, so the
actual DOM structure can be inspected instead of guessed at. Prints to
stdout only - not written to any committed file or artifact.

Usage:
    python debug_detail_page.py <listing_url>
"""
import sys

from playwright.sync_api import sync_playwright


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.mudah.my/tri-pinnacle-114681845.htm"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            )
        )
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000)

        print("=" * 80)
        print(f"URL: {url}")
        print(f"Page title: {page.title()}")

        print("=" * 80)
        print("ALL BUTTONS on page (text | outerHTML truncated):")
        buttons = page.locator("button")
        for i in range(min(buttons.count(), 40)):
            b = buttons.nth(i)
            try:
                text = (b.inner_text() or "").strip().replace("\n", " ")
                html = b.evaluate("el => el.outerHTML")[:200]
                print(f"  [{i}] text={text!r} html={html!r}")
            except Exception as e:
                print(f"  [{i}] error: {e}")

        print("=" * 80)
        print("ALL <a> LINKS whose text or href mentions phone/call/contact/whatsapp/chat:")
        links = page.locator("a")
        for i in range(min(links.count(), 200)):
            a = links.nth(i)
            try:
                text = (a.inner_text() or "").strip().replace("\n", " ")
                href = a.get_attribute("href") or ""
                blob = (text + " " + href).lower()
                if any(k in blob for k in ["phone", "call", "contact", "whatsapp", "wa.me", "chat"]):
                    print(f"  [{i}] text={text!r} href={href!r}")
            except Exception:
                continue

        print("=" * 80)
        print("Elements whose OWN text (not children) matches phone/call/contact-ish words:")
        matches = page.evaluate(
            """
            () => {
                const re = /phone|call|contact|whatsapp|advertiser|seller/i;
                const out = [];
                for (const el of document.querySelectorAll('body *')) {
                    const own = Array.from(el.childNodes)
                        .filter(n => n.nodeType === 3)
                        .map(n => n.textContent.trim())
                        .join(' ')
                        .trim();
                    if (own && re.test(own) && own.length < 120) {
                        out.push({tag: el.tagName, cls: (el.className || '').toString().slice(0,80), text: own});
                    }
                }
                return out.slice(0, 60);
            }
            """
        )
        for m in matches:
            print(f"  <{m['tag']} class={m['cls']!r}> {m['text']!r}")

        print("=" * 80)
        print("Clicking any button/link with reveal-ish text, then re-dumping phone-like content...")
        reveal_selector = (
            "button:has-text('Show'), a:has-text('Show'), "
            "button:has-text('Call'), a:has-text('Call'), "
            "button:has-text('Phone'), a:has-text('Phone'), "
            "button:has-text('Contact'), a:has-text('Contact'), "
            "button:has-text('Chat'), a:has-text('Chat')"
        )
        try:
            reveal_buttons = page.locator(reveal_selector)
            n = min(reveal_buttons.count(), 5)
            print(f"Found {n} reveal-ish controls")
            for i in range(n):
                btn = reveal_buttons.nth(i)
                text = (btn.inner_text() or "").strip()
                print(f"  clicking [{i}] {text!r}")
                try:
                    btn.click(timeout=3000, force=True)
                    page.wait_for_timeout(1500)
                except Exception as e:
                    print(f"    click failed: {e}")
        except Exception as e:
            print(f"reveal search failed: {e}")

        print("=" * 80)
        print("Body text AFTER clicks, lines containing digits (potential phone) or short (potential name):")
        body_text = page.locator("body").inner_text()
        for line in body_text.split("\n"):
            line = line.strip()
            if line and any(c.isdigit() for c in line) and len(line) < 40:
                print(f"  DIGIT-LINE: {line!r}")

        browser.close()


if __name__ == "__main__":
    main()
