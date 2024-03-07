import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import discord
import json

class OilersScrape:
    def __init__(self):
        self.json_db = "database/oilersscrape.json"
        with open(self.json_db, 'r') as file:
            self.db = json.load(file)
        self.url = "https://www.nhl.com/oilers/video/topic/highlights/"
        self.base_url = "https://www.nhl.com"

    def get_highlights(self):
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.find_all("a", class_="nhl-c-card-wrap -customentity -video", href=True)
        highlights = []
        for result in results:
            if "HIGHLIGHTS" not in result["aria-label"]:
                continue
            if result["href"] not in self.db["highlights_href"]:
                highlights.append(result["href"])
                self.db["highlights_href"][result["href"]] = result["aria-label"].split('| ')[-1]
        return highlights

    def write_db(self):
        # Used over __del__ so that with errors this isn't called.
        with open(self.json_db, 'w') as file:
            json.dump(self.db, file)

    def run(self, channel):
        # Get highlights from a game that has finished.
        highlights = self.get_highlights()

        self.write_db()
        return highlights


os = OilersScrape()
print(os.run("111"))