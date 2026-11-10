import hashlib
import hmac
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

STEAM_API = os.environ["STEAM_API_KEY"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["ADMIN_ID"]
STEAM_IDS = [s.strip() for s in os.environ["STEAM_IDS"].split(",") if s.strip()]
#RUST_APPID = "252490"
RUST_APPID = "570"
STATE = Path("state.json")


def key_for(steamid: str) -> str:
    return hmac.new(BOT_TOKEN.encode(), steamid.encode(), hashlib.sha256).hexdigest()[:20]


def fetch_players() -> list[dict]:
    params = urllib.parse.urlencode({"key": STEAM_API, "steamids": ",".join(STEAM_IDS)})
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?{params}"
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)["response"]["players"]


def send(text: str) -> None:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=json.dumps({"chat_id": CHAT_ID, "text": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=20).close()


def main() -> None:
    if not STEAM_IDS:
        print("List empty(git)")
        return

    old = json.loads(STATE.read_text()) if STATE.exists() else None
    new = dict(old or {})
    messages = []

    try:
        players = fetch_players()
    except Exception as e:
        print("Steam unavailable(git):", type(e).__name__)
        return

    for p in players:
        key = key_for(p["steamid"])
        in_rust = p.get("gameid") == RUST_APPID
        if old is not None and key in old and old[key] != in_rust:
            messages.append(
                f"🟢 {p['personaname']} in Rust(git)" if in_rust
                else f"🔴 {p['personaname']} out of Rust (git)"
            )
        new[key] = in_rust

    try:
        for m in messages:
            send(m)
    except Exception as e:
        print("No messages to Telegram:(git)", type(e).__name__)
        return

    STATE.write_text(json.dumps(new))
    print("OK")


if __name__ == "__main__":
    main()
