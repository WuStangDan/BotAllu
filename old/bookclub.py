from replit import db
from tabulate import tabulate


def parse_message(msg):
    """
    Determines which internal function to pass the book club message to.

    Args:
        msg (str): The book club message.

    Returns:
        bool or str: False indicates failure and to keep the message and send a warning. A string indicates success and the leaderboard should be updated.
    """
    if msg.startswith("add "):
        return add(msg[4:])
    elif msg.startswith("[add] "):
        return add(msg[6:])
    elif msg.startswith("update "):
        return update(msg[7:])
    elif msg.startswith("remove "):
        return remove(msg[7:])
    elif msg.startswith("[remove] "):
        return remove(msg[9:])
    return False


def status_str(num):
    """
    Converts a status number to a corresponding status string.

    Args:
        num (int or str): The status number.

    Returns:
        str: The corresponding status string.
    """
    # Filter out square brackets.
    if isinstance(num, str):
        num = num.split("[")[-1]
        num = num.split("]")[0]

    num = int(num)
    if num == -1:
        return ":x:"
    if 0 <= num < 25:
        return ":clock12:"
    if 25 <= num < 50:
        return ":clock3:"
    if 50 <= num < 75:
        return ":clock6:"
    if 75 <= num < 100:
        return ":clock9:"
    if num == 100:
        return ":white_check_mark:"
    return None


def progress():
    """
    Generates the progress string representing the leaderboard.

    Returns:
        str: The progress string.
    """
    progress_str = "`" + db["bookclub"]["game_name"] + "\n"
    # Add underline.
    progress_str += "_" * len(progress_str) + "`\n"

    players = db["bookclub"]["players"]
    for player in players:
        progress_str += status_str(players[player]) + " "
        progress_str += "`" + player + "`\n"

    progress_str += "\n` * !bookclub newgame GAMENAME"
    progress_str += "\n * !bookclub add PLAYER"
    progress_str += "\n * !bookclub update PLAYER#[0,25,50,75,100]. Ex. Ender#75"
    progress_str += "\n * !bookclub bump`"
    return progress_str


def add(player):
    """
    Places a Discord user into the leaderboard.

    Args:
        player (str): The name of the player.

    Returns:
        str: The updated progress string representing the leaderboard.
    """
    db["bookclub"]["players"][player] = -1
    return progress()


def remove(player):
    """
    Removes a Discord user from the leaderboard.

    Args:
        player (str): The name of the player.

    Returns:
        bool or str: False if the player is not found, otherwise the updated progress string representing the leaderboard.
    """
    players = db["bookclub"]["players"]
    if player in players:
        del players[player]
        return progress()
    else:
        return False


def update(player_status):
    """
    Updates the status of a player in the leaderboard.

    Args:
        player_status (str): The player name and status in the format 'PLAYER#STATUS'.

    Returns:
        bool or str: False if the input format is invalid or the status is unknown, otherwise the updated progress string representing the leaderboard.
    """
    player_status = player_status.split("#")

    # Verify input contains player name and status.
    if len(player_status) < 2:
        return False
    player = player_status[0]
    status = player_status[1]

    # Check that status is sensible.
    if status_str(status) is None:
        return False
    db["bookclub"]["players"][player] = status
    return progress()
