def to_json(_dict):
    output = {}
    for key in _dict.keys():
        if type(_dict[key]) == replit.database.database.ObservedDict:
            output[key] = to_json(_dict[key])
        else:
            output[key] = str(_dict[key])
    return output
with open("database_backup.json", "w") as file:
  json.dump(to_json(db), file, indent=2)