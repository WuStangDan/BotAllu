from replit import db
from tabulate import tabulate

def parse_message(msg):
  """
  parse_message determines which internal function to pass the bookclub message too.

  return: False indicates failure and to keep message and send warning. String indicates sucess and leaderboard should be updated.
  """
  if msg[0:4] == "add ":
    return add(msg[4:])
  elif msg[0:7] == "update ":
    return update(msg[7:])
  elif msg[0:7] == "remove ":
    return remove(msg[7:])

  return False


def status_str(num):
  num = int(num)
  if num == -1:
    return ':x:'
  if num == 0:
    return ':clock12:'
  if num == 25:
    return ':clock3:'
  if num == 50:
    return ':clock6:'
  if num == 75:
    return ':clock9:'
  if num == 100:
    return ':white_check_mark:'
  return None

def progress():
  progress_str = '`' + db['bookclub']['game_name'] + '\n'
  # Add underline.
  for i in range(len(progress_str)):
    progress_str += '_'
  progress_str += '`\n'

  d = db['bookclub']['players']
  for player in d:
    progress_str += status_str(d[player]) + ' '
    progress_str += '`' + player
    progress_str += '`\n'
  
  progress_str += '\n` * !bookclub newgame GAMENAME'
  progress_str += '\n * !bookclub [add,remove] PLAYER'
  progress_str += '\n * !bookclub update PLAYER#[0,25,50,75,100]`'
  return progress_str

def add(player):
  """
  add Places a discord user into the board.
  """
  db['bookclub']['players'][player] = -1
  return progress()

def remove(player):
  """
  add Removes a discord user from the board.
  """
  if player in db['bookclub']['players']:
    del db['bookclub']['players'][player]
    return progress()
  else:
    return False

def update(player_status):
  player_status = player_status.split('#')

  # Verify input contains player name and status.
  if len(player_status) < 2:
    return False
  player = player_status[0]
  status = player_status[1]

  # Check that status is sensical.
  if status_str(status) == None:
    return False
  db['bookclub']['players'][player] = status
  return progress()