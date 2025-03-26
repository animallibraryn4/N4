import requests
from bs4 import BeautifulSoup
import os

# User-Agent ताकि वेबसाइट हमें ब्लॉक न करे
HEADERS = {"User-Agent": "Mozilla/5.0"}

# एनीमे लिस्ट निकालने के लिए फंक्शन
def get_anime_list():
    URL = "https://anime-world.co/"
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    anime_list = []
    for anime in soup.select(".animelist a"):
        title = anime.text.strip()
        link = anime["href"]
        anime_list.append({"title": title, "link": link})
    
    return anime_list

# किसी एक एनीमे के एपिसोड लिंक्स निकालने के लिए फंक्शन
def get_episode_links(anime_page_url):
    response = requests.get(anime_page_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    episodes = []
    for ep in soup.select(".episodelist a"):
        ep_title = ep.text.strip()
        ep_link = ep["href"]
        episodes.append({"title": ep_title, "link": ep_link})
    
    return episodes

# वीडियो डाउनलोड करने के लिए फंक्शन
def download_video(video_url, save_path="downloaded_video.mp4"):
    response = requests.get(video_url, stream=True)
    
    with open(save_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)

    return save_path  # डाउनलोड की गई फाइल का नाम वापस करेगा

# टेस्ट के लिए
if __name__ == "__main__":
    anime_list = get_anime_list()
    print("Anime List:", anime_list[:5])  # पहले 5 एनीमे प्रिंट करेंगे
    
    if anime_list:
        episodes = get_episode_links(anime_list[0]["link"])
        print("Episodes of first anime:", episodes[:5])  # पहले 5 एपिसोड प्रिंट करेंगे
        
        if episodes:
            print("Downloading first episode...")
            video_file = download_video(episodes[0]["link"])
            print("Downloaded:", video_file)
