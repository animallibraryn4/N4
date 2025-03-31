from AnilistPython import Anilist

anilist = Anilist()

def getAnimeInfo(query):
    try:
        id = anilist.get_anime_id(query)
        anime = anilist.get_anime_with_id(id)

        img = f"https://img.anili.st/media/{id}"

        # Common data with safe defaults
        name_romaji = anime.get("name_romaji", "N/A")
        name_english = anime.get("name_english", name_romaji)
        _type = anime.get("airing_format", "N/A")
        status = anime.get("airing_status", "N/A")
        episodes = anime.get("airing_episodes", "N/A")
        score = anime.get("average_score", "N/A")
        genres = ", ".join(anime.get("genres", [])) or "N/A"
        desc = anime.get("desc", "No synopsis available.")
        
        # Handle potentially missing dates and duration
        start_date = anime.get("starting_time", "N/A")
        end_date = anime.get("ending_time", "N/A")
        duration = f"{anime.get('duration', 'N/A')} minutes" if anime.get('duration') else "N/A"

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

‣ **Genres:** {genres}
‣ **Type:** {_type}
‣ **Average Rating:** {score}
‣ **Status:** {status}
‣ **First aired:** {start_date}
‣ **Last aired:** {end_date}
‣ **Runtime:** {duration}
‣ **No of episodes:** {episodes}

‣ **Synopsis:** {desc}

(Source: AniList)
"""

        return img, text1, text2

    except Exception as e:
        error_msg = f"Error fetching anime info: {str(e)}"
        return None, error_msg, error_msg
