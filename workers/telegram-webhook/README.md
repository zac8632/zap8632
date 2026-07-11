# Telegram Webhook Worker

Replaces polling (`getUpdates` on a `*/10 * * * *` GitHub Actions cron,
which was measured to actually run ~2 hours late on average - GitHub
throttles `schedule` triggers) with a real Telegram webhook. Telegram POSTs
each new message here the instant it arrives; this Worker authenticates the
request and immediately fires a `repository_dispatch` event, which GitHub
starts within seconds. All the actual parsing/batching/photo-download logic
still lives in `scripts/listings-pipeline/telegram_listings.py` - this
Worker is a thin, dumb relay, on purpose, so a bug in the real logic only
ever needs a Python fix, not a Worker redeploy.

## One-time setup (only you can do these - they need your own accounts)

### 1. Cloudflare API token

1. Go to <https://dash.cloudflare.com/profile/api-tokens> → **Create Token**.
2. Use the **Edit Cloudflare Workers** template (or a custom token with
   `Account.Workers Scripts: Edit` permission).
3. Copy the token.
4. Also grab your **Account ID** - it's shown on the right side of any zone
   overview page in the Cloudflare dashboard, or on
   <https://dash.cloudflare.com> under **Workers & Pages**.

### 2. A GitHub Personal Access Token for the Worker to call back with

The Worker runs outside GitHub Actions, so it can't use the automatic
`GITHUB_TOKEN` - it needs its own token to call the `repository_dispatch`
API.

1. <https://github.com/settings/tokens> → **Generate new token (classic)**.
2. Scope: **`repo`** (repository_dispatch needs full repo scope on classic
   tokens - fine-grained tokens have had inconsistent support for this
   endpoint).
3. Copy the token.

### 3. A random webhook secret (you generate this yourself, any strong random string)

This is just a shared secret so the Worker can verify a request genuinely
came from Telegram and not from someone who guessed your Worker's URL.
Any long random string works, e.g. run `openssl rand -hex 32` locally, or
use a password generator.

### 4. Add all of these as repo secrets

**Settings → Secrets and variables → Actions → Secrets tab → New repository secret:**

| Secret name | Value |
|---|---|
| `CLOUDFLARE_API_TOKEN` | from step 1 |
| `CLOUDFLARE_ACCOUNT_ID` | from step 1 |
| `GH_DISPATCH_TOKEN` | from step 2 |
| `TELEGRAM_WEBHOOK_SECRET` | from step 3 |

(`TELEGRAM_BOT_TOKEN` already exists from the earlier Inbox Bot setup -
reused here, nothing new needed for it.)

### 5. Deploy

Once all four secrets above are in place, trigger the **Deploy Telegram
Webhook Worker** workflow (Actions tab → select it → Run workflow). It
will:
- Deploy the Worker to Cloudflare
- Push `TELEGRAM_SECRET_TOKEN`/`GH_DISPATCH_TOKEN` into the Worker's own
  secret store (separate from the GitHub secrets above - Cloudflare needs
  its own copy)
- Register the deployed URL as the Telegram bot's webhook
- Print `getWebhookInfo` at the end so you can see it's live

That's it - from then on, every message sent to the bot triggers the Inbox
Bot workflow within seconds instead of waiting for the next poll.

## Reverting to polling

If you ever want to go back to polling (e.g. to debug without the Worker in
the way): call `https://api.telegram.org/bot<TOKEN>/deleteWebhook`, then run
the Inbox Bot workflow manually with `mode: poll`.
