from typing import Any, Dict, Optional
import requests


class Y2mate:
    def __init__(self):
        self.base_url = "https://www.y2mate.com"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
        }

    def ajax(self, url):
        base_url = "https://www.y2mate.com"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
        }

        data = {
            "k_query": url,
            "k_page": "home",
            "hl": "en",
            "q_auto": 0,
        }
        data = "&".join([f"{key}={value}" for key, value in data.items()])

        resp = requests.post(
            url=base_url + "/mates/en872/analyzeV2/ajax", headers=headers, data=data
        )

        return resp.json()

    def convert(self, post_data) -> Dict[str, Any]:
        data = "&".join([f"{key}={value}" for key, value in post_data.items()])
        headers = {
            "authority": "www.y2mate.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": "_ga=GA1.1.884534433.1701337493; _ga_PSRPB96YVC=GS1.1.1701337492.1.1.1701338604.0.0.0",
            "origin": "https://www.y2mate.com",
            "pragma": "no-cache",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        resp = requests.post(
            url=self.base_url + "/mates/convertV2/index", headers=headers, data=data
        )
        return resp.json()

    def yt(self, url, type="mp3") -> Optional[Dict[str, Any]]:
        ajax_data = self.ajax(url)
        rexp = "128kbps" if type == "mp3" else "^(480|720)p"
        result = {}
        links = list(ajax_data["links"][type].items())
        video = next(
            (v for v in links if v[1]["f"] == type and rexp in v[1]["q"]), None
        )
        if video is not None:
            video = video[1]
            result["q"] = video["q"]

            post_data = {
                "vid": ajax_data["vid"],
                "k": video["k"].replace("=", ""),
            }
            convert_data = self.convert(post_data)
            return {**result, **convert_data}
        else:
            return None


# Example usage:
y2mate = Y2mate()
