import requests
import json
from tabulate import tabulate


class StatsFFXIV:
    def __init__(self):
        self.basu_name = "Basu Tew"
        self.basu_id = 42543529
        self.server = "Midgardsormr"
        self.xiv_api = "https://xivapi.com/character/"
        self.highest_job = {}

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

    def get_highest_level_class(self, name, id):
        # For a lodgestone ID, enter name and highest job level into db.
        # This function is called outside of this class so this class doesn't need to be declared async.
        # This is because lodgestone has a 1 api call per second rate limit.
        response = requests.get(self.xiv_api + str(id))
        if response.status_code != 200:
            return
        character_data = json.loads(response.text)['Character']
        highest_level_class = ['', 0]
        # The first 20 classes are the non-crafting classes.
        for job in character_data['ClassJobs'][:20]:
            if job['Level'] > highest_level_class[1]:
                self.highest_job[name] = {}
                self.highest_job[name]['level'] = job['Level']
                job_name = job['Name']
                if job['Level'] >= 30:
                    # Jobs higher than 30 use second name.
                    job_name = job['Name'].split('/')[1]
                else:
                    job_name = job['Name'].split('/')[0]
                self.highest_job[name]['job'] = job_name.strip().title()
                self.highest_job[name]['xp_bar'] = job['ExpLevel']/job['ExpLevelMax']

    def generate_stats_table(self):
        # Create the output that will fill the discord message.
        headers = ['','Job','Level','XP Bar']
        table = []
        for name, info in self.highest_job.items():
            row = [name]
            row += [info['job']]
            row += [info['level']]
            xp_bar = '|' + '█' * int(info['xp_bar']*10)
            xp_bar = xp_bar.ljust(11) + '|'
            row += [xp_bar]

            table += [row]
        
        # Sort by level, descending.
        table.sort(reverse=True, key=lambda x: (x[2], x[3], x[0]))

        message = tabulate(table, headers=headers, colalign=("left","right","right","right"))
        # Ticks required for discord fixed width.
        return '`' + message + '`'