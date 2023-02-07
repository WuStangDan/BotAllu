import requests
import json
from tabulate import tabulate
from pytz import timezone
from datetime import datetime
from PIL import Image
import math
import io
import os
import asyncio


class MaintenanceFFXIV:
    def __init__(self, db):
        self.api_url = 'https://lodestonenews.com/news/maintenance?locale=NA&limit=5'
        self.db = db
        if 'post_ids' not in self.db:
            self.db['post_ids'] = {}

    def get_maintenance(self):
        response = requests.get(self.api_url)
        response = json.loads(response.text)
        for post in response:
            if 'All Worlds' not in post['title']:
                # Not world maintenance.
                continue
            if post['id'] in self.db['post_ids']:
                # Already posted.
                continue
            self.db['post_ids'][post['id']] = 'posted'
            latest_all_world = '`' + post['title']
            if post['start'] is None:
                # No start and end time supplied.
                return latest_all_world + '`'
            strp = '%Y-%m-%dT%H:%M:%S%z'
            start = datetime.strptime(post['start'], strp)
            alberta_time = timezone('MST7MDT')
            strf = '%a %b %d %I:%M %p'
            start = start.astimezone(alberta_time)
            start = start.strftime(strf)
            latest_all_world += ' ' + start
            if post['end'] is None:
                # No end time.
                return latest_all_world + ' MST`'
            end = datetime.strptime(post['end'], strp)
            end = end.astimezone(alberta_time)
            end = end.strftime(strf[3:])
            latest_all_world += ' to ' + end + ' MST`'
            return latest_all_world
        return None


class StatsFFXIV:
    def __init__(self):
        self.basu_name = "Basu Tew"
        self.basu_id = 42543529
        self.server = "Midgardsormr"
        self.xiv_api = "https://xivapi.com/character/"
        self.highest_job = {}
        self.photos = {}

    def get_names_and_id(self):
        # Get the names and IDs of all Basu Tews friends.
        response = requests.get(self.xiv_api + str(self.basu_id) + "?data=FR")
        if response.status_code != 200:
            return
        name_and_id = {}
        name_and_id[self.basu_name] = self.basu_id
        friends = json.loads(response.text)["Friends"]
        for friend in friends:
            name_and_id[friend["Name"]] = friend["ID"]
        return name_and_id

    def get_highest_level_job(self, name, id):
        # For a lodgestone ID, enter name and highest job level into db.
        # This function is called outside of this class so this class doesn't need to be declared async.
        # This is because lodgestone has a 1 api call per second rate limit.
        response = requests.get(self.xiv_api + str(id))
        if response.status_code != 200:
            return
        character_data = json.loads(response.text)['Character']
        self.photos[name] = character_data['Avatar']
        self.highest_job[name] = {'level': 0}
        # The first 20 classes are the non-crafting classes.
        for job in character_data['ClassJobs'][:20]:
            if job['Level'] > self.highest_job[name]['level']:
                self.highest_job[name]['level'] = job['Level']
                job_name = job['Name']
                if job['Level'] >= 30:
                    # Jobs higher than 30 use second name.
                    job_name = job['Name'].split('/')[1]
                else:
                    job_name = job['Name'].split('/')[0]
                self.highest_job[name]['job'] = job_name.strip().title()
                self.highest_job[name][
                    'xp_bar'] = job['ExpLevel'] / job['ExpLevelMax']

    def generate_stats_table(self):
        # Create the output that will fill the discord message.
        headers = ['', 'Highest Job', 'Level', 'XP Bar']
        table = []
        for name, info in self.highest_job.items():
            row = [name]
            row += [info['job']]
            row += [info['level']]
            xp_bar = '|' + '█' * int(info['xp_bar'] * 10)
            xp_bar = xp_bar.ljust(11) + '|'
            row += [xp_bar]

            table += [row]

        # Sort by level, descending.
        table.sort(reverse=True, key=lambda x: (x[2], x[3], x[0]))
        self.table = table

        message = tabulate(table,
                           headers=headers,
                           colalign=("left", "right", "right", "right"))
        # Ticks required for discord fixed width.
        return '`' + message + '`'

    def image_to_byte_array(self, image: Image):
        # Converts PIL Image into byte array.
        imgByteArr = io.BytesIO()
        image.save(imgByteArr, format='JPEG')
        imgByteArr = imgByteArr.getvalue()
        return imgByteArr

    async def upload_group_photo(self):
        images_in_row = 4
        num_rows = math.ceil(len(self.photos) / images_in_row)
        group_photo = Image.new('RGB', (424 * images_in_row, 493 * num_rows))
        photos = []

        for row in self.table:
            photos_url = self.photos[row[0]]
            photos_url = photos_url.split('?')[0][:-12]
            photos_url += 'l0_640x873.jpg'
            photos += [Image.open(requests.get(photos_url, stream=True).raw)]
            # (left, top, right, bottom)
            photos[-1] = photos[-1].crop((108, 46, 532, 539))
            # Sleep to not overload lodgestone rate limit.
            await asyncio.sleep(2)

        # Combine photos.
        for c in range(num_rows):
            for r in range(images_in_row):
                if len(photos) == 0:
                    break
                group_photo.paste(photos.pop(0), (424 * r, 493 * c))

        imgur_url = "https://api.imgur.com/3/image"

        payload = {"image": self.image_to_byte_array(group_photo)}
        headers = {
            'Authorization': 'Client-ID ' + os.environ['IMGUR_CLIENT_ID']
        }

        response = requests.request("POST",
                                    imgur_url,
                                    headers=headers,
                                    data=payload,
                                    files=[])
        self.group_photo_url = json.loads(response.text)['data']['link']
