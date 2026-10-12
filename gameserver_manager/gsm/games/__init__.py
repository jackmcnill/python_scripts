from .minecraft import Minecraft

GAMES = {g.id: g for g in (Minecraft(),)}


def get_game(game_id):
    try:
        return GAMES[game_id]
    except KeyError:
        raise KeyError(f"Unbekanntes Spiel '{game_id}'") from None
