import os
from collections import deque
import re

class Event:
	def __init__(self, t, log_name):
		self.type = t
		self.log_name = log_name
		self.location = None # xxx
	
	def length(self):
		return 0

class CastEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("CastEvent", log_name)
		self.turn_no = turn_no
		self.content = lines

		if "You lose 1 Adventure" in lines:
			self._length = 1
			print("cast", turn_no)
		else:
			self._length = 0

	def length(self):
		return self._length

class BannerEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("BannerEvent", log_name)
		self.content = lines

class Encounter:
	def __init__(self, lines):
		self.content = lines
		if lines == []:
			raise ValueError("NO")
		self.name = lines[0][len('Encounter: '):]
		self.name = self.name

class AdventureEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("AdventureEvent", log_name)
		self.content = lines
		self.last_turn = turn_no

		parsed = re.match("\\[([0-9]*)\\] (.*)", lines[0])
		if parsed == None:
			raise ValueError("NO")

		self.turn_no = int(parsed[1])
		self._length = self.turn_no - turn_no

		self.location = parsed[2]
		self.encounters = []
		
		if len(lines) == 1:
			return # We have no encounters. Don't process any!

		last_encounter = 0
		index = None
		for index, line in enumerate(lines[1:]):
			if line.startswith('Encounter:'):
				if last_encounter != 0:
					self.encounters.append(Encounter(lines[last_encounter:index+2]))
				last_encounter = index+1

		self.encounters.append(Encounter(lines[last_encounter:index+2]))
		
		# Sometimes, Mafia groups the initial NC and the wheel NC under one event. We don't split them as that requires effort.
		# Treat it as one long adventure.
		
		if self.location == "The Castle in the Clouds in the Sky (Top Floor)":
			found_wheel = False
			for e in self.encounters:
				if e.name == "Keep On Turnin' the Wheel in the Sky":
					found_wheel = True
			if len(self.encounters) > 1 and found_wheel:
				self._length = 2
		
		# Shore hack
		if self.location == "The Shore, Inc. Travel Agency":
			if "You lose 3 Adventures" in self.content:
				self._length = 3
			else:
				self._length = 0

		# Sometimes, Mafia groups multiple mining adventures under one event. We don't split them as that requires effort.
		# Treat it as one long adventure.
		if self.location == "Itznotyerzitz Mine (in Disguise)":
			self._length = len(self.content)-1

	def length(self):
		return self._length

# TODO: ... everything else?

class ItemEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("ItemEvent", log_name)
		self.content = lines

class ShopEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("ShopEvent", log_name)
		self.content = lines

class ClosetEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("ClosetEvent", log_name)
		self.content = lines

class EquipEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("EquipEvent", log_name)
		self.content = lines

class CraftEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("CraftEvent", log_name)
		self.content = lines

class ConsumeEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("ConsumeEvent", log_name)
		self.content = lines

class ShrugEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("ShrugEvent", log_name)
		self.content = lines

class PullEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("PullEvent", log_name)
		self.content = lines

class BuffEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("BuffEvent", log_name)
		self.content = lines

class FamiliarEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("FamiliarEvent", log_name)
		self.content = lines

class PermEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("PermEvent", log_name)
		self.content = lines

class MeatEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("MeatEvent", log_name)
		self.content = lines

class PHPEvent(Event):
	def __init__(self, log_name, turn_no, lines):
		super().__init__("PHPEvent", log_name)
		self.content = lines
		
		# XXX: Ew.
		# This handles Ed going to the Underworld from his base. We add the adventure here because detecting the other way around is more of a pain.
		if self.content[0] == 'place.php?whichplace=edbase&action=edbase_portal' and self.content[1] == 'Encounter: Like a Bat Into Hell':
			self._length = 1
		else:
			self._length = 0

		self.turn_no = turn_no + self._length

	def length(self):
		return self._length

class Ascension:
	def __init__(self, events):
		# TODO: This goes a bit weird when we process the first log if it doesn't start at the start of an adventure.
		self.events = events
		self.name = "No idea"
		self.path = "unknown"

		for ev in self.events:
			if ev.type == "BannerEvent" and ev.content[0] == 'Beginning New Ascension':
				self.name = ev.content[1]
				self.path = ev.content[2]
				break

	def __str__(self):
		return "{} {}".format(self.name, self.path)

	def __repr__(self):
		return self.__str__()

class Log:
	def __init__(self, file):
		self.name = file
		print(file)
		self.file = open(file, 'r')
		self.events = []

		ignore = False

		lines = deque(self.file.readlines())
		log_line = ""
		self.current_event = []
		self.current_banner = []
		banner_count = 0

		self.current_turn_no = 0
		while len(lines) != 0:
			log_line = lines.popleft()
			log_line = log_line.strip()
			
			# Mafia sometimes prints
			# --------------------
			# stuff
			# --------------------
			# If a line only contains - characters, ignore until the next line only containing - characters
			if set(log_line) == set("-"):
				ignore = not ignore
				continue

			if ignore:
				continue
			
			# Mafia (mostly....) signals a new event with an empty line.
			if log_line == '':
				# If we're in a banner, skip handling this (empty) line.
				if banner_count != 0:
					continue

				# If we have event data, handle it!
				if self.current_event != []:
					self.process_event()
					self.current_event = []

				# If we have banner data, handle it!
				if self.current_banner != []:
					self.events.append(BannerEvent(self.name, self.current_turn_no, self.current_banner))
					self.current_banner = []
			# Mafia uses this pattern to indicate the start / middle / end of a banner.
			elif log_line == '=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=':
				banner_count += 1
				# if we're at the end of a banner, reset the banner counter
				if banner_count == 3:
					banner_count = 0
			else:
				# if we're inside a banner, don't handle the line as an event.
				if banner_count != 0:
					self.current_banner.append(log_line)
				# otherwise, it's a normal event line and all is well
				else:
					self.current_event.append(log_line)

		# We might have an event left at the end of the log, so let's process that.
		if self.current_event != []:
			self.process_event()
			self.current_event = []

	def process_event(self):
		php_regex = re.compile("^[^.]*\.php")
		# Here, we key off the first part of the line. Mafia is fairly regular, thankfully.
		event_map = {
			"send a kmail": "ignore",
			"cast": CastEvent,
			"use": ItemEvent,
			"Use": ItemEvent,
			"Visiting": "ignore",
			"autosell": ShopEvent,
			"add to closet": ClosetEvent,
			"take from closet": ClosetEvent,
			"[": AdventureEvent,
			"trading": ShopEvent,
			"Trade": ShopEvent,
			"buy": ShopEvent,
			"Buy": ShopEvent,
			"equip": EquipEvent,
			"Talking to": "ignore",
			"Create": CraftEvent,
			"Combine": CraftEvent,
			"eat": ConsumeEvent,
			"drink": ConsumeEvent,
			"chew": ConsumeEvent,
			"Inspecting": "ignore",
			"Tower":  "ignore",
			"uneffect": ShrugEvent,
			"pull": PullEvent,
			"concert": BuffEvent,
			"familiar": FamiliarEvent,
			"Welcome to Valhalla": "ignore", # XXX
			"Softcore perm": PermEvent,
			"Hardcore perm": PermEvent,
			"Return": "ignore",
			"Ascend": "ignore",
			"friars": BuffEvent,
			"You gain": MeatEvent,
			"maximize": "ignore",
			"#": "ignore",
			"feed": "ignore",
			"Leaflet": "ignore",
			"Entering": "ignore", # Nemesis: This is broken, why?
			"Examining": "ignore", # also broken lol
			"Investigating": "ignore", # Dakota Fanning, this is broken
			"grandpa": "ignore", # XXX: Sea
			"send": "ignore"
		}

		found = False
		skipped = False
		current_event = self.current_event

		for key in event_map:
			if current_event[0].startswith(key):
				if event_map[key] != None:
					found = True
					if event_map[key] != 'ignore':
						# XXX: This sucks. Make it more general.
						broken_encounter = False
						bar_match = re.match("\\[([0-9]*)\\] Cap'm Caronch's Map", current_event[0])
						if bar_match != None:
							print("Found a usage of Cap'm Caronch's Map - fixing if mafia broke it...")
							for line in current_event:
								if line == "Encounter: This Adventure Bites":
									print("Found double encounter!")
									idx = current_event.index("Encounter: This Adventure Bites")
									before = current_event[:idx]
									after = current_event[idx:]
									synthetic_turn_no = int(bar_match[1]) + 1
									after.insert(0, "[{}] Barrney's Barr".format(synthetic_turn_no))
									# Manually add the turn that did occur correctly.
									self.events.append(event_map[key](self.name, self.current_turn_no, before))
									self.current_turn_no += 1

									# Treat it as if we just found the missing turn. We know it's an encounter.
									last_ev = event_map["["](self.name, self.current_turn_no, after)
									broken_encounter = True
									break

						bridge_troll = "Encounter: hulking bridge troll" in current_event

						# Sometimes it gets recorded properly. Sometimes it doesn't.
						if bridge_troll and not "Orc Chasm" in current_event[0]:
							idx = current_event.index("Encounter: hulking bridge troll")
							before = current_event[:idx]
							after = current_event[idx:]
							before_ev = event_map[key](self.name, self.current_turn_no, before)
							self.current_turn_no += before_ev.length()
							self.events.append(before_ev)
							self.current_turn_no += 1

							after.insert(0, "[{}] Orc Chasm".format(self.current_turn_no))
							# Treat it as if we just found the missing turn. We know it's an encounter.
							last_ev = event_map["["](self.name, self.current_turn_no, after)
							broken_encounter = True

						# If we are handling a 
						if not broken_encounter:
							last_ev = event_map[key](self.name, self.current_turn_no, self.current_event)
					else:
						skipped = True
				else:
					print("nope", current_event)
		# If we got an event..
		if found:
			# and we want to handle it
			if not skipped:
				# handle it!
				# If the event gives us a turn count, use it.
				self.current_turn_no += last_ev.length()
				self.events.append(last_ev)
		else:
			php_result = re.match(php_regex, current_event[0])
			if php_result != None:
				# Yes, place.php can cost adventures! (ed base)
				php_ev = PHPEvent(self.name, self.current_turn_no, self.current_event)
				self.current_turn_no += php_ev.length()
				self.events.append(php_ev)
			else:
				print("Unhandled event", current_event)
				print("Bug Stary about it.")
				exit()

def unfuck_log(advs, fix=True):	
	print("unfucking", len(advs), "events")

	really_last = advs[0]
	last_adv = advs[1]

	# TODO: this probably works better as a for loop iterating and slicing as it goes, instead of 3 variables...

	for i, a in enumerate(advs[2:]):
		diff = a.turn_no - last_adv.turn_no
		diff_2 = last_adv.turn_no - really_last.turn_no

		if diff != last_adv.length() and diff_2 != really_last.length():
			if really_last.type == "AdventureEvent" and last_adv.type == "AdventureEvent" and a.type == "AdventureEvent":
				if last_adv.location == 'The Shore, Inc. Travel Agency' and (diff == 3 or diff == 0):
					pass
				else:
					# Mafia duplicates a turn and skips two later to make up for it.
					# 0 0 2
					if diff == 2 and diff_2 == 0:
						if fix:
							print("Fixing a (positive) missed turn!", a.log_name, really_last.turn_no, last_adv.turn_no, a.turn_no, really_last.location, last_adv.location, a.location, really_last.length(), last_adv.length(), a.length())
							last_adv.turn_no += 1
							last_adv._length = 1
							a._length = 1
						else:
							print("Found a (positive) missed turn after fixing - Mafia probably screwed up.\nPlease try to add the missing markers manually.", last_adv.turn_no, a.turn_no, a.log_name, last_adv.location, a.location)
							exit()
					# Mafia skips two turns, then duplicates to make up for it.
					# 0 2 2
					elif diff == 0 and diff_2 == 2:
						if fix:
							print("Fixing a (negative) missed turn!", a.log_name, really_last.turn_no, last_adv.turn_no, a.turn_no, really_last.location, last_adv.location, a.location, really_last.length(), last_adv.length(), a.length())
							a.turn_no += 1
							last_adv._length = 1
							a._length = 1
						else:
							print("Found a (negative) missed turn after fixing - Mafia probably screwed up.\nPlease try to add the missing markers manually.", last_adv.turn_no, a.turn_no, a.log_name, last_adv.location, a.location)
							exit()
					# This probably shouldn't happen and indicates Weird(tm).
					elif diff != 0 and diff_2 != 0:
						print("Hmmm, another kind of mismatch. (fix={})".format(fix))
						print(a.log_name)
						print(really_last.location, last_adv.location, a.location)
						print(really_last.turn_no, last_adv.turn_no, a.turn_no)
						print(really_last.length(), last_adv.length(), a.length())
						#exit()

		really_last = last_adv
		last_adv = a

class LogReader:
	def __init__(self, log_dir):
		self.log_dir = log_dir
		self.logs = []

		logs = os.listdir(log_dir)
		logs.sort()
		
		# Process all of the logs we have.
		for l in logs:
			log_path = log_dir + "/" + l
			if os.path.isfile(log_path) and not "active_session" in log_path:
				self.logs.append(Log(log_path))

		self.ascensions = []
		new_ascension_index = None
		current_ascension = []
		
		# Iterate over the logs, putting together ascensions as we go.
		for l in self.logs:
			# TODO: is there a better way we can do this?
			found_new_ascension = False
			for i, ev in enumerate(l.events):
				if ev.type == 'PHPEvent' and ev.content[0].startswith('ascend.php'):
					current_ascension.extend(l.events[:i])
					self.ascensions.append(Ascension(current_ascension))

					new_ascension_index = i
					current_ascension = []
					found_new_ascension = True
					break

			if not found_new_ascension:
				current_ascension.extend(l.events)
			else:
				current_ascension.extend(l.events[new_ascension_index:])

		self.ascensions.append(Ascension(current_ascension))
		for asc in self.ascensions:
			advs = [ev for ev in asc.events if ev.type == "AdventureEvent" or ev.type == "PHPEvent" or ev.type == "CastEvent"]
			unfuck_log(advs)
			unfuck_log(advs, fix=False)
