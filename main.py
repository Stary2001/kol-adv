#!/usr/bin/python3

import kol

logs = kol.LogReader("sessions")
for asc in logs.ascensions:
    advs = [ev for ev in asc.events if ev.type == "AdventureEvent" or ev.type == "PHPEvent" or ev.type == "CastEvent"]
    for a in advs:
        if a.type != "PHPEvent" or (a.content[0].startswith("place.php")):
            print(a.turn_no, a.content[0])
