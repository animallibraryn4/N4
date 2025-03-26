import requests
import json
import urllib


def IndexScrapper(url):
    payload = {"page_token": "", "page_index": 0}
    payload = json.dumps(payload)

    url = f"{url}/" if url[-1] != "/" else url

    headers = {"Referer": "https://aatdl.xyz/archives/9222"}

    response = requests.post(url, data=payload, headers=headers)

    if "Worker threw exception" in response.text:
        raise Exception("Worker threw exception")

    response = response.json()

    file_length = len(response["data"]["files"])
    result = []

    for i, _ in enumerate(range(file_length)):
        files_type = response["data"]["files"][i]["mimeType"]
        if files_type != "application/vnd.google-apps.folder":
            files_name = response["data"]["files"][i]["name"]
            direct_download_link = url + urllib.parse.quote(files_name)
            result.append((files_name, direct_download_link))
    return result
