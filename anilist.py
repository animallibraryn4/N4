from AnilistPython import Anilist

anilist = Anilist()

def get_anime_info(query):
    try:
        anime_id = anilist.get_anime_id(query)
        anime = anilist.get_anime_with_id(anime_id)
        
        img_url = f"https://img.anili.st/media/{anime_id}"
        
        name_romaji = anime.get("name_romaji", "N/A")
        name_english = anime.get("name_english", name_romaji)
        
        text = f"**{name_english}**"
        if name_english != name_romaji:
            text += f" ({name_romaji})"
            
        text += f"""
━━━━━━━━━━━━━━━━━━━━
📺 **Type:** `{anime.get('airing_format', 'N/A')}`
🕒 **Status:** `{anime.get('airing_status', 'N/A')}`
🎬 **Episodes:** `{anime.get('airing_episodes', 'N/A')}`
⭐ **Score:** `{anime.get('average_score', 'N/A')}/100`
🔮 **Genres:** `{', '.join(anime.get('genres', []))}`
━━━━━━━━━━━━━━━━━━━━
"""
        return img_url, text
        
    except Exception as e:
        raise Exception(f"AniList error: {str(e)}")
