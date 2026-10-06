"""Score board: finish times with the players' team name, kept in scores.json.

Every finished run that gets a name is stored (nothing is ever thrown away);
rankings are made per map and player count, fastest first. scores.json looks like
    {"scores": [{"name": "MeEeEe", "map": "Cave", "players": 2,
                 "time": 83.46, "date": "2026-10-06 14:03"}, ...]}
A missing or broken file never crashes the game: it is treated as empty, and a
broken file is kept as scores.json.broken instead of being overwritten.
"""
import datetime
import json
import os

import config

SCORES_FILE = os.path.join(config.ROOT, "scores.json")
NAME_MAX = 16               # longest team name (characters)


class ScoreBoard:
    def __init__(self, path=SCORES_FILE):
        self.path = path
        self.scores = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, encoding="utf-8") as f:
                rows = json.load(f)["scores"]
            # keep only rows that have everything with the right type
            return [r for r in rows if isinstance(r, dict)
                    and isinstance(r.get("name"), str) and isinstance(r.get("map"), str)
                    and isinstance(r.get("players"), int) and isinstance(r.get("time"), (int, float))]
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"scores.json could not be read ({e}); starting an empty score board")
            try:
                os.replace(self.path, self.path + ".broken")    # keep it for a human to look at
            except OSError:
                pass
            return []

    def _save(self):
        # write to a temporary file first, then swap it in: a crash half-way
        # through writing can never leave a cut-off scores.json behind
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"scores": self.scores}, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError as e:
            print(f"scores.json could not be saved ({e})")

    def add(self, name, map_name, players, time):
        """Store a finished run and save the file. Returns the new row."""
        row = {"name": name.strip()[:NAME_MAX] or "?", "map": map_name, "players": players,
               "time": round(time, 2), "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
        self.scores.append(row)
        self._save()
        return row

    def ranking(self, map_name, players):
        """All runs on this map with this many players, fastest first."""
        rows = [r for r in self.scores if r["map"] == map_name and r["players"] == players]
        return sorted(rows, key=lambda r: r["time"])

    def best(self, map_name, players):
        """Fastest time so far, or None."""
        rows = self.ranking(map_name, players)
        return rows[0]["time"] if rows else None
