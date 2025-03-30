from AnilistPython import Anilist

anilist = Anilist()


def getAnimeInfo(query):
    id = anilist.get_anime_id(query)
    anime = anilist.get_anime_with_id(id)

    img = f"https://img.anili.st/media/{id}"

    name_romaji = anime["name_romaji"]
    name_english = anime["name_english"]

    _type = anime["airing_format"]
    status = anime["airing_status"]
    episodes = anime["airing_episodes"]
    score = anime["average_score"]
    genres = ", ".join(anime["genres"])

    if name_english != name_romaji:
        text = f"**{name_english} - ({name_romaji})**"
    else:
        text = f"**{name_english}**"

    text += f"""
━━━━━━━━━━━━━━━━━━━━
📺 **Type :** `{_type}`
🕒 **Status :** `{status}`
🎬 **Episodes :** `{episodes}`
⭐ **Score :** `{score}`
🔮 **Genres :** `{genres}`
━━━━━━━━━━━━━━━━━━━━
📥 **Watch / Download : SD ┃ HD ┃ FHD**
━━━━━━━━━━━━━━━━━━━━
"""
    return img, text
