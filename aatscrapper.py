import requests
from bs4 import BeautifulSoup as bs
import urllib


def get_anime_urls(url):
    r = requests.get(url)
    soup = bs(r.content, "html.parser")
    anime_data = {}

    anime_data["title"] = (
        soup.find("div", "entry-content clear").find("h2").text.strip(" !")
    )
    anime_data["links"] = []

    for div in soup.find_all("div", "bg-margin-for-link"):
        q = div.find("a", "bg-showmore-plg-link").text
        if "FHD" in q:
            q = "FHD"
        elif "HD" in q:
            q = "HD"
        elif "SD" in q:
            q = "SD"

        d = []

        links = div.find("div").find_all("a")
        for link in links:
            d.append(link["href"])

        anime_data["links"].append((q, d))

    return anime_data


# print(get_anime_urls(
#     "https://animeacademy.in/berserk-kenpuu-denki-berserk-hindi-subbed-01-25/"
# )
# )


def fix_url(url):
    x, y = url.split("/0:/")
    return x + "/0:/" + urllib.parse.quote(y)


def get_index_urls(url):
    r = requests.get(url, allow_redirects=False)
    soup = bs(r.text, "html.parser")

    indexUrls = []

    for i in soup.find_all("iframe"):
        src = i["src"]
        src = fix_url(src)
        indexUrls.append(src)

    return indexUrls
