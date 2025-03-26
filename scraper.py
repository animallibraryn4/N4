import requests
from bs4 import BeautifulSoup
from config import ANIME_WORLD_URL, HEADERS

# Function to Get Anime List
def get_anime_list():
    response = requests.get(ANIME_WORLD_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    anime_list = []
    for anime in soup.select(".animelist a"):
        title = anime.text.strip()
        link = anime["href"]
        anime_list.append({"title": title, "link": link})
    
    return anime_list

# Function to Get Episode Links for an Anime
def get_episode_links(anime_page_url):
    response = requests.get(anime_page_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    episodes = []
    for ep in soup.select(".episodelist a"):
        ep_title = ep.text.strip()
        ep_link = ep["href"]
        episodes.append({"title": ep_title, "link": ep_link})
    
    return episodes

# Function to Download Video
def download_video(video_url, save_path="downloaded_video.mp4"):
    response = requests.get(video_url, stream=True)
    
    with open(save_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)

    return save_path  # Returns the Downloaded File Name

# Test the Scraper
if __name__ == "__main__":
    anime_list = get_anime_list()
    print("Anime List:", anime_list[:5])  # Prints the First 5 Animes
    
    if anime_list:
        episodes = get_episode_links(anime_list[0]["link"])
        print("Episodes of First Anime:", episodes[:5])  # Prints First 5 Episodes
        
        if episodes:
            print("Downloading First Episode...")
            video_file = download_video(episodes[0]["link"])
            print("Downloaded:", video_file)
