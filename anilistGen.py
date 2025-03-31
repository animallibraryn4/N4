from AnilistPython import Anilist

anilist = Anilist()


def getAnimeInfo(query):
    id = anilist.get_anime_id(query)
    anime = anilist.get_anime_with_id(id)

    img = f"https://img.anili.st/media/{id}"

    name_romaji = anime["name_romaji"]
    name_english = anime["name_english"]
    
    # Formatting the name
    if name_english != name_romaji:
        title = f"{name_english} | {name_romaji}"
    else:
        title = name_english

    # Getting all details
    genres = ", ".join(anime["genres"])
    _type = anime["airing_format"]
    score = anime["average_score"]
    status = anime["airing_status"]
    start_date = anime["starting_time"]
    end_date = anime["ending_time"]
    episodes = anime["airing_episodes"]
    duration = "24 minutes"  # Assuming standard anime episode length
    desc = anime["desc"]

    # First message - Basic info
    info_msg = f"""
{title}

‣ Genres : {genres}
‣ Type : {_type}
‣ Average Rating : {score}
‣ Status : {status}
‣ First aired : {start_date}
‣ Last aired : {end_date}
‣ Runtime : {duration}
‣ No of episodes : {episodes}
"""

    # Second message - Synopsis
    synopsis_msg = f"""
‣ Synopsis : {desc}

(Source: Crunchyroll)
"""

    return img, info_msg, synopsis_msg
