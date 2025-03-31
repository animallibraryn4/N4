from AnilistPython import Anilist
from datetime import datetime

anilist = Anilist()

def getAnimeInfo(query):
    id = anilist.get_anime_id(query)
    anime = anilist.get_anime_with_id(id)

    img = f"https://img.anili.st/media/{id}"

    # Common data
    name_romaji = anime["name_romaji"]
    name_english = anime["name_english"]
    _type = anime["airing_format"]
    status = anime["airing_status"]
    episodes = anime["airing_episodes"]
    score = anime["average_score"]
    genres = ", ".join(anime["genres"])
    desc = anime["desc"]
    start_date = anime["starting_time"]
    end_date = anime["ending_time"]
    duration = anime["duration"]  # in minutes

    # Format 1 (Original Compact Format)
    if name_english != name_romaji:
        text1 = f"**{name_english} - ({name_romaji})**"
    else:
        text1 = f"**{name_english}**"

    text1 += f"""
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

    # Format 2 (Detailed Format)
    text2 = f"""
**{name_english} | {name_romaji}**

‣ **Genres :** {genres}
‣ **Type :** {_type}
‣ **Average Rating :** {score}
‣ **Status :** {status}
‣ **First aired :** {start_date}
‣ **Last aired :** {end_date}
‣ **Runtime :** {duration} minutes
‣ **No of episodes :** {episodes}

‣ **Synopsis :** {desc}

(Source: AniList)
"""

    return img, text1, text2
