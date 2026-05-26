# Twitch & IGDB запросы
import requests
from config import TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET
from translator import translate

_token_cache = {}


def get_token() -> str:
    if _token_cache.get("token"):
        return _token_cache["token"]
    r = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials",
    })
    r.raise_for_status()
    _token_cache["token"] = r.json()["access_token"]
    return _token_cache["token"]


def _h() -> dict:
    return {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {get_token()}",
    }


# 1.IGDB: поиск игры
def search_game(name: str) -> str:
    body = f'search "{name}"; fields name,summary,rating,genres.name,platforms.name; limit 1;'
    r = requests.post("https://api.igdb.com/v4/games", headers=_h(), data=body)
    games = r.json()
    if not games:
        return "Игра не найдена."
    g = games[0]
    rating = f"{g.get('rating', 0):.1f}/100" if g.get("rating") else "нет рейтинга"
    genres = ", ".join(x["name"] for x in g.get("genres", [])) or "—"
    platforms = ", ".join(x["name"] for x in g.get("platforms", [])) or "—"

    raw_summary = (g.get("summary") or "").strip()
    # Переводим полный текст, потом обрезаем — иначе обрезанный текст плохо переводится
    summary = translate(raw_summary)[:400] if raw_summary else "—"

    return (
        f"🎮 *{g['name']}*\n"
        f"⭐ Рейтинг: {rating}\n"
        f"🎭 Жанры: {genres}\n"
        f"🖥 Платформы: {platforms}\n"
        f"📝 {summary}…"
    )


# 2.IGDB: топ-10 игр для платформы
def top_games(platform_name: str) -> str:
    r = requests.post(
        "https://api.igdb.com/v4/platforms",
        headers=_h(),
        data=f'search "{platform_name}"; fields id,name; limit 1;',
    )
    platforms = r.json()
    if not platforms:
        return f"Платформа «{platform_name}» не найдена."
    pid, pname = platforms[0]["id"], platforms[0]["name"]

    r2 = requests.post(
        "https://api.igdb.com/v4/games",
        headers=_h(),
        data=(
            f"fields name,rating; where platforms = ({pid}) & rating != null; "
            "sort rating desc; limit 10;"
        ),
    )
    games = r2.json()
    if not games:
        return "Игры не найдены."
    lines = [f"🏆 *Топ-10 для {pname}*\n"]
    for i, g in enumerate(games, 1):
        lines.append(f"{i}. {g['name']} — {g.get('rating', 0):.1f}/100")
    return "\n".join(lines)


# 3.Twitch: статус стримера
def streamer_status(login: str) -> str:
    r = requests.get(
        "https://api.twitch.tv/helix/streams",
        headers=_h(),
        params={"user_login": login},
    )
    data = r.json().get("data", [])
    if not data:
        return f"🔴 Стример *{login}* сейчас офлайн."
    s = data[0]
    return (
        f"🟢 *{login}* стримит!\n"
        f"🎮 Игра: {s.get('game_name', '—')}\n"
        f"📺 {s.get('title', '—')}\n"
        f"👥 Зрителей: {s['viewer_count']:,}"
    )


# 4.Twitch: топ клипов по игре
def game_clips(game_name: str) -> str:
    r = requests.get(
        "https://api.twitch.tv/helix/games",
        headers=_h(),
        params={"name": game_name},
    )
    games = r.json().get("data", [])
    if not games:
        return f"Игра «{game_name}» не найдена в Twitch."
    gid = games[0]["id"]
    gname = games[0]["name"]

    r2 = requests.get(
        "https://api.twitch.tv/helix/clips",
        headers=_h(),
        params={"game_id": gid, "first": 5},
    )
    clips = r2.json().get("data", [])
    if not clips:
        return f"Клипы по игре *{gname}* не найдены."

    lines = [f"🎬 *Топ клипов — {gname}*\n"]
    for c in clips:
        lines.append(f"• *{c['broadcaster_name']}*: [{c['title']}]({c['url']}) — 👁 {c['view_count']:,}")
    return "\n".join(lines)
