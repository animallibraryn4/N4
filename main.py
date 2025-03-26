from scraper import get_anime_list, get_episode_links, download_video
from bot import send_video_to_telegram

def main():
    anime_list = get_anime_list()
    if not anime_list:
        print("No anime found.")
        return
    
    for anime in anime_list[:1]:  # Only process the first anime (for testing)
        episodes = get_episode_links(anime["link"])
        
        if not episodes:
            print(f"No episodes found for {anime['title']}")
            continue
        
        for ep in episodes[:1]:  # Only download the first episode (for testing)
            print(f"Downloading: {ep['title']}")
            video_path = download_video(ep["link"])
            
            if video_path:
                print(f"Uploading {ep['title']} to Telegram...")
                send_video_to_telegram(video_path, ep["title"])
                print("Upload complete!")

if __name__ == "__main__":
    main()
