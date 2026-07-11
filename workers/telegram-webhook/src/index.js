/**
 * Telegram webhook receiver for the Inbox Bot pipeline.
 *
 * Telegram POSTs each new message here the instant it arrives (instead of
 * this repo polling getUpdates every N minutes - see .github/workflows/
 * inbox-bot.yml for why that was slow: GitHub throttles `schedule`
 * triggers, measured at ~2 hours average delay for a 10-minute cron on this
 * repo). This Worker's only job is to authenticate the request really came
 * from Telegram, then immediately fire a `repository_dispatch` event so
 * GitHub Actions - which already has all the real processing logic in
 * scripts/listings-pipeline/telegram_listings.py - picks it up within
 * seconds. No business logic lives here; a bug in the batching/parsing
 * logic should only ever need a Python fix, not a Worker redeploy.
 *
 * Required secrets (set via `wrangler secret put`, see
 * .github/workflows/deploy-telegram-webhook.yml):
 *   TELEGRAM_SECRET_TOKEN - matches the secret_token given to Telegram's
 *     setWebhook call; Telegram echoes it back on every request as the
 *     X-Telegram-Bot-Api-Secret-Token header, so this rejects anyone who
 *     isn't Telegram (or doesn't know the secret) with 401.
 *   GH_DISPATCH_TOKEN - a GitHub PAT (repo scope, or fine-grained
 *     Actions:write + Contents:read on this one repo) used to call the
 *     GitHub REST API from outside Actions - the built-in GITHUB_TOKEN
 *     only exists inside a running workflow, not out here.
 *
 * Plain vars (set in wrangler.toml, not secret):
 *   GH_OWNER, GH_REPO - the repository to dispatch to.
 */

const DISPATCH_EVENT_TYPE = "telegram-update";

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    const url = new URL(request.url);
    if (url.pathname !== "/telegram-webhook") {
      return new Response("Not Found", { status: 404 });
    }

    const secretHeader = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (!env.TELEGRAM_SECRET_TOKEN || secretHeader !== env.TELEGRAM_SECRET_TOKEN) {
      // Deliberately vague response - don't help an attacker distinguish
      // "wrong secret" from "no secret configured".
      return new Response("Unauthorized", { status: 401 });
    }

    let update;
    try {
      update = await request.json();
    } catch (e) {
      return new Response("Bad Request: invalid JSON", { status: 400 });
    }

    if (!update || typeof update !== "object" || !("update_id" in update)) {
      // Telegram's own Update schema always has update_id - anything else
      // isn't a real Telegram update, reject rather than forward garbage
      // into the GitHub Actions pipeline.
      return new Response("Bad Request: not a Telegram Update", { status: 400 });
    }

    if (!env.GH_DISPATCH_TOKEN || !env.GH_OWNER || !env.GH_REPO) {
      console.error("Worker misconfigured: missing GH_DISPATCH_TOKEN/GH_OWNER/GH_REPO");
      // Still 200 to Telegram - a config error on our end shouldn't make
      // Telegram think THIS delivery failed and needs retrying forever;
      // log it here for us to notice and fix instead.
      return new Response("OK (misconfigured - see Worker logs)", { status: 200 });
    }

    const dispatchResp = await fetch(
      `https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "penang-telegram-webhook-worker",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_type: DISPATCH_EVENT_TYPE,
          client_payload: { update },
        }),
      }
    );

    if (!dispatchResp.ok) {
      const bodyText = await dispatchResp.text();
      console.error(`GitHub dispatch failed: ${dispatchResp.status} ${bodyText}`);
      // Same reasoning as above - don't make Telegram retry over a
      // GitHub-side failure it can't do anything about.
      return new Response(`OK (dispatch failed upstream: ${dispatchResp.status})`, { status: 200 });
    }

    return new Response("OK", { status: 200 });
  },
};
