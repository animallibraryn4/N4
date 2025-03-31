from AnilistPython import Anilist

anilist = Anilist()

def getAnimeInfo(query):
    try:
        id = anilist.get_anime_id(query)
        anime = anilist.get_anime_with_id(id)

        img = f"https://img.anili.st/media/{id}"

        # Extract data safely
        name_romaji = anime.get("name_romaji", "N/A")
        name_english = anime.get("name_english", name_romaji)
        _type = anime.get("airing_format", "N/A")
        status = anime.get("airing_status", "N/A")
        episodes = anime.get("airing_episodes", "N/A")
        score = anime.get("average_score", "N/A")
        genres = ", ".join(anime.get("genres", [])) or "N/A"
        desc = anime.get("desc", "No synopsis available.")
        start_date = anime.get("starting_time", "N/A")
        end_date = anime.get("ending_time", "N/A")
        duration = f"{anime.get('duration', 'N/A')} min" if anime.get('duration') else "N/A"

        # Format 1 (Compact)
        text1 = f"**{name_english}** ({name_romaji})" if name_english != name_romaji else f"**{name_english}**"
        text1 += f"""
━━━━━━━━━━━━━━━━━━━━
📺 **Type:** `{_type}`
🕒 **Status:** `{status}`
🎬 **Episodes:** `{episodes}`
⭐ **Score:** `{score}`
🔮 **Genres:** `{genres}`
━━━━━━━━━━━━━━━━━━━━
📥 **Watch/Download:** SD | HD | FHD
━━━━━━━━━━━━━━━━━━━━"""

        # Format 2 (Detailed)
        text2 = f"""
**{name_english} | {name_romaji}**

‣ **Genres:** {genres}
‣ **Type:** {_type}
‣ **Rating:** {score}
‣ **Status:** {status}
‣ **Aired:** {start_date} to {end_date}
‣ **Runtime:** {duration}
‣ **Episodes:** {episodes}

📜 **Synopsis:**  
{desc}

(Source: AniList)
"""

        def getAnimeInfo(query):
    try:
        # ... (same data fetching as before) ...

        # Combine both formats into one message
        combined_text = f"{text1}\n\n━━━━━━━━━━━━━━━━━━━━\n📜 **DETAILED INFO**\n━━━━━━━━━━━━━━━━━━━━\n{text2}"

        return img, combined_text  # Only 2 values returned

    except Exception as e:
        return None, f"⚠️ Error: {str(e)}"  # Still returns 2 values
