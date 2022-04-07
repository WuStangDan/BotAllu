from ffxiv import StatsFFXIV
import time

a = StatsFFXIV()
b = a.get_names_and_id()
for name, id in b.items():
    time.sleep(2)
    a.get_highest_level_job(name, id)
a.generate_stats_table()
a.save_group_photo()