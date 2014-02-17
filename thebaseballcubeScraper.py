#!/usr/bin/env python3.3

# thebaseballcubeScraper.py
# Simon Swanson
# takes in stats from thebaseballcube.com and exports to an XML file for future use


# BeautifulSoup for parsing the HTML
# re for all the regexing that needs to be done while searching the HTML
# get for pulling the HTML down
# sys for argv
from bs4 import BeautifulSoup
import re
from requests import get
import sys


# players that throw errors are saved into a global dictionary to be spit out later
# better way to do this? probably. Haven't thought of one though
warningPlayers = {}


# might be worth looking into something like getOpt as more options are added
def argParse(args, leagues):
	'''Takes in system args and turns them into a list of useable strings or errors out.'''

	# print('Starting argParse')

	# default value with no arguments is to scrape mlb player data
	if not args:
		return ['mlb']

	leagueDict = {'majors': 'mlb', 'milb': 'minors', 'ncaa': 'college'}
	# loops through all arguments to find which leagues should be looked at
	# makes sure never to double-count any leagues so I don't run the same thing twice
	for arg in args:
		if arg in leagueDict.values():
			if arg not in leagues:
				leagues.append(arg)
		elif arg in leagueDict.keys():
			if leagueDict[arg] not in leagues:
				leagues.append(leagueDict[arg])

		# if any of the arguments doesn't work, errors out
		else:
			print('ERROR: "{}" is not a valid argument.'.format(arg))
			print('\nValid arguments:')
			print('  "mlb" or "majors" for major league information')
			print('  "milb" or "minors" for minor league information')
			print('  "ncaa" or "college" for college player information - feature in progress')
			print('\n  EXAMPLE: "{} minors majors" retrieves data on active players that have not made it to the major leagues and all active players that have made it to the major leagues.'.format(sys.argv[0]))
			sys.exit(1)

	return leagues


def indexParse(league):
	'''Opens the index URL and finds the links to letter-based indexes based on the leagues given.'''

	# print('Starting indexParse')

	soup = BeautifulSoup(get('http://www.thebaseballcube.com/players/').text)
	# mlb players are under the div.letters tag, minors and college players are under the div.otherPlayers tag
	# retrieves all links that lead to an index of last names
	if league == 'mlb':
		links = soup.select('div.letters a[href^="mlb"]')
	else:
		# currently the > operator works college links aren't active
		links = soup.select('div.otherPlayers > a[href^={}]'.format(league))

	return links


def letterParse(links, profiles):
	'''Takes in a list of links to letters and finds all non-retired players from them.'''

	# print('Starting letterParse')

	for link in links:
		# soup = BeautifulSoup(get('mlb.asp?L=a').text)
		soup = BeautifulSoup(get('http://www.thebaseballcube.com/players/{}'.format(link.get('href'))).text)
		# all players are under the pre tag, active players are distinguished by including the b tag
		# retrieves all links that lead to an active player's profile
		for profile in soup.select('pre b a[href^="profile"]'):
			profiles.append(profile)

	return profiles


def profileParse(profiles):
	'''Takes in a list of links to profiles and turns all needed information to an XML format.'''

	# print('Starting profileParse')
	
	# initializes the XML and prepares the file for writing
	xml = BeautifulSoup(features='xml')
	xml.append(xml.new_tag('Players'))


	# updates the XML for each player
	# debate: when to write to file? I doubt my RAM can take everything
	i = 1
	for profile in profiles:
		link = profile.get('href')
		soup = BeautifulSoup(get('http://thebaseballcube.com/players/{}'.format(link)).text)
		xml = playerInfo(xml, soup)
		
		# # currently writing to file every 50 just to make sure it all works correctly
		# i += 1
		# if (i % 200) == 0:
		# 	print('Writing to file.')
		# 	output.write(xml.prettify())
		# 	print('Done writing to file. Continuing')

	print('Finishing!')
	output = open('All_Player_Information.xml', 'w')	
	output.write(xml.prettify())
	print('Written to file.')

	return xml


def playerInfo(xml, soup):
	'''Finds all basic information on the player and adds it to an XML document.'''

	# print('Starting playerInfo')

	# finds the playe's personal information that will be used to identiy then later on
	playerInfo = personalInfo(soup)

	# the player's stats for his main position is in the first statsCategories1 div tag
	# the string in the statsCategories1 div tag shows whether the player is primarily a pitcher or batter
	mainPosition = soup.find('div', class_='statsCategories1').string

	# if the player is a pitcher or batter, retrieves the correct stats and updates the xml
	# otherwise throws a warning, stores the player's name and ID, and continues
	if 'PITCHING' in mainPosition:
		stats = pitcherParse(soup)
		xml = pitcherXML(playerInfo, stats, xml)
	elif 'BATTING' in mainPosition:
		stats = hitterParse(soup)
		xml = hitterXML(playerInfo, stats, xml)
	
	else:
		playerName = playerInfo['FullName']
		playerID = playerInfo['PlayerID']
		warningPlayers[playerID] = playerName
		print('{} caused a problem. Continuing.'.format(playerName))

	return xml


def personalInfo(soup):
	'''Finds all the basic personal information about the player as a dictionary.'''

	# print('Starting PersonalInfo')

	# stores in a dictionary
	info = {}
	info['FullName'] = infoSearch(soup, 'Full Name')
	info['PlayerID'] = infoSearch(soup, 'TBC Player ID')
	info['Birthday'] = infoSearch(soup, 'Born', 'a')
	# the available attribute is set to yes when the player is created
	# will come up with a way to modify the attribute as I figure out how to work this during the season
	info['Available'] = 'Yes'
	print('Player {} (TBCID {}) is now being processed.'.format(info['FullName'], info['PlayerID']))
	
	return info


def infoSearch(soup, match, subtag = None):
	'''Retrieves basic player information from the TBC header based on the string (and tag) given.'''

	# print('Starting infoSearch')

	# the information needed is in the div tag after the identifying div tag, as given by the matching string
	tag = soup.find('div', class_='cat1', text=match).findNextSibling('div')
	
	# for birthdays there is an a tag to go through before the string can be extracted
	if subtag:
		tag = tag.find(subtag)

	# after navigating to the correct location in the tree, extracts the string contained and cleans the whitespace
	# apparently some players don't have birthdays entered, so I need to account for that
	try:
		info = tag.string.strip()
	except:
		info = 'Unknown'

	return info


def pitcherParse(soup):
	'''Takes in a pitcher profile and adds the appropriate information to a dictionary.'''

	# print('Starting pitcherParse')

	# lists of all the stats that come from the different sections
	basicList = ['BB', 'Bk', 'CG', 'ER', 'G', 'GS', 'H', 'HR', 'IP', 'L', 'Level', 'SH', 'SO', 'SV', 'W', 'WP', 'Year']
	advancedList = ['HB', 'Level', 'Year']
	extraList = ['BS', 'HLD', 'IBB', 'InR', 'InS', 'Level', 'QS', 'Year']
	fullPitcherList = ['BB', 'BS', 'Bk', 'CG', 'ER', 'G', 'GS', 'H', 'HB', 'HLD', 'HR', 'IBB', 'IP', 'InR', 'InS', 'L', 'QS', 'SH', 'SO', 'SV', 'W', 'WP']

	# the primary stats table is the first table with the stats class, with each row under a tr tag
	# the other stats are in the same location under different URLs
	mainStats = tableTrim(soup.find('table', class_='stats'))
	advancedStats = tableTrim(profileLink(soup, 'AdvancedP', 'Advanced').find('table', class_='stats'))
	extraStats = tableTrim(profileLink(soup, 'ExtraP', 'Extra').find('table', class_='stats'))

	# stats are stored as a dictionary of years with subdictionaries by levels for easy access
	stats = {}
	stats = updateStats(mainStats, basicList, stats)
	stats = updateStats(advancedStats, advancedList, stats)
	stats = updateStats(extraStats, extraList, stats)

	# makes sure all stats have an entered value for each year and level
	stats = statVerify(stats, fullPitcherList)

	return stats


def hitterParse(soup):
	'''Takes in a hitter profile and adds the appropriate information to a dictionary.'''

	# print('Starting hitterParse')

	# list of all the stats that come from the different sections
	hittingList = ['2B', '3B', 'BB', 'CS', 'DP', 'G', 'H', 'HBP', 'HR', 'IBB', 'Level', 'PA', 'R', 'RBI', 'SB', 'SF', 'SH', 'SO', 'Year']
	fieldingList = ['E', 'G', 'Level', 'Position', 'Year']
	fullHitterList = ['2B', '3B', 'BB', 'CS', 'DP', 'E', 'G', 'H', 'HBP', 'HR', 'IBB', 'PA', 'Positions', 'R', 'RBI', 'SB', 'SF', 'SH', 'SO']

	# the first table will be hitting information
	hittingStats = tableTrim(soup.find('table', class_='stats'))

	# the fielding table is located as a sibling to the last div tag with the statsCategories1 class
	# the table is the next sibling table tag
	fielding = soup.findAll('div', class_='statsCategories1')[-1]
	fieldingStats = tableTrim(fielding.findNextSibling('table'))

	# stats are stored as a dictionary of years with subdictionaries by levels for easy access
	stats = {}
	stats = updateStats(hittingStats, hittingList, stats)
	stats = updateStats(fieldingStats, fieldingList, stats, fielding = True)

	return stats


def profileLink(soup, linkText, tagText):
	'''Retrieves the contents of a URL from a player profile based on the link URL and tag text'''

	# print('Starting profileLink')

	# the separate pages of the player profile are in the href of an a tag 
	link = soup.find('a', href=re.compile(r'.+Page={}'.format(linkText)), text=tagText)['href']
	newSoup = BeautifulSoup(get('http://thebaseballcube.com/players/{}'.format(link)).text)

	return newSoup


def tableTrim(table):
	'''Cleans stat tables of all entries that are not regular season stats or the header.'''

	# print('Starting tableTrim')

	# the header is identified by headerRow should be the first entry in the table
	header = table.find('tr', class_='headerRow')

	# the summary stats are found under the footerRow or footerRowNotBold entry
	footer = table.find('tr', class_=re.compile(r'footerRow\w*'))

	# trims both ends of the table
	trimmedTable = table.findAll('tr')
	trimmedTable = trimmedTable[trimmedTable.index(header):]

	if footer in trimmedTable:
		trimmedTable = trimmedTable[:trimmedTable.index(footer)]

	return trimmedTable


def findIndices(header, items):
	'''Takes in the header of the table and matches the index of the stat in the header with the name of the stat.'''
	# no solution for minor leaguers as of yet...

	# print('Starting findIndices')

	# breaks the header into a list of tags that only contain stats
	tagBreak = header.findAll('td')

	# loops through all the elements to find the correct indices
	# assumes the all the elements exists (which I should have accounted for already)
	stats = {}
	for item in items:
		statTag = header.find('td', text=item)
		
		# because pitcher extra stats do not include a level, accounts for that situation when the stat is not in the header
		if statTag in tagBreak:
			index = tagBreak.index(statTag)
			stats[item] = index
		else:
			stats[item] = 'MLB'

	return stats


def updateStats(table, statList, stats, fielding = False):
	'''Using the indices given, extracts the appropriate stats from each year and puts them into a dictionary'''
	# sinfully long function

	# print('Starting updateStats')

	# finds the indices for all the items in the list of needed statistics by comparing to the header section of the table
	indices = findIndices(table[0], statList)

	# holds onto the indicies for the stats that aren't used in the main stat section
	# deletes so I can freely loop over all remaining stats
	# hacky -- should be a better way to do this
	yearIndex = indices['Year']
	levelIndex = indices['Level']
	del(indices['Year'], indices['Level'])
	statList.remove('Year')
	statList.remove('Level')

	# for each part of the table (which is broken into unique teams per year) extracts all the necessary stats and updates the dictionary 
	for teamStats in table[1:]:

		# breaks the table into td tags for easy stat access
		team = teamStats.findAll('td')

		# extracts the year and the level from the information to use as identifying information
		# if the year doesn't exist, it lies under the previous year, so it won't update the year
		# should always work for first year so there should always be a year to use
		if team[yearIndex].string.strip():
			year = team[yearIndex].string.strip()

		# deals with the problem of pitcher Extra stats not having a level to reference
		if levelIndex == 'MLB':
			level = levelIndex
		else:
			level = team[levelIndex].string.strip()

		# make sure that no information is being overwritten
		# adds year and level if it is a new year
		if year not in stats.keys():
			stats[year] = {}
			stats[year][level] = {}
		
		# adds the level if it doesn't exist
		# otherwise all the information for the subdictionaries exists and nothing needs to be done on this level
		elif level not in stats[year].keys():
			stats[year][level] = {}

		yearLevel = stats[year][level]

		# fielding stats are stored in a special sub-dictionary to avoid overwriting games played stats
		if fielding:
			positionIndex = indices['Position']
			stats = updateFieldingStats(team, indices, stats, year, level, positionIndex)

		# goes through all stats in the dictionary and pulls out their value
		else:
			for statName in indices.keys():
				value = team[indices[statName]]
				# need to use contents because some stats are clickable and have subtags
				try:
					statValue = value.string.strip()
				except:
					try:
						statValue = value.contents[0].string.strip()
					except:
						statValue = '0'

				# some stats are left blank or unknown by TBC, so inserted a fix
				if statValue == '--':
					statValue = '0'

				# if the stat is already entered for that year and level, adds the old number to the new number to find the total (possible because I have all counting stats)
				if statName in yearLevel.keys():
					oldValue = tryFloat(yearLevel[statName])
					# converts back to a string from an int for consistency and because XML takes strings
					statValue = str(oldValue + tryFloat(statValue))

				yearLevel[statName] = statValue

			# makes sure a value is entered for each possible stat
			for year in stats.keys():
				for level in stats[year].keys():
					for stat in statList:
						if stat not in stats[year][level].keys():
							stats[year][level][stat] = '0'
	
	return stats


def updateFieldingStats(team, indices, stats, year, level, positionIndex):
	'''Takes in fielding stats and adds to a dictionary or some shit'''

	# print('Starting updateFieldingStats')

	yearLevel = stats[year][level]

	# creates the positions subdictionary where information will be stored
	# the dictionary is named by the position name
	if 'Positions' not in yearLevel.keys():
		yearLevel['Positions'] = {}

	position = team[positionIndex].string.strip()
	yearLevel['Positions'][position] = {}
	fielding = yearLevel['Positions'][position]

	# loops through the other values and stores them under the position subdictionary
	for statName in indices.keys():

		# DH has blank stats, so this works around the problem by assigning values to 0
		try:
			statValue = team[indices[statName]].string.strip()
		except:
			statValue = '0'

		# in case the stats have already been entered (which I don't think is possible, but just in case)
		if statName in fielding.keys():
			oldValue = tryFloat(fielding[statName])
			# converts back to a string from an int for consistency and because XML takes strings
			statValue = str(oldValue + tryFloat(statValue))

		fielding[statName] = statValue

	return stats


def pitcherXML(playerInfo, stats, xml):
	'''Finds position-specific information for pitchers and sends the information to be entered in the XML.'''

	# print('Starting pitcherXML')

	# determines the number of games for each type of pitching from last season (at the highest level the player played)
	# adds the information to playerInfo
	previousSeason = sorted(stats.keys())[-1]
	level = sortLevels(stats[previousSeason])[-1]
	games = stats[previousSeason][level]['G']
	starts = stats[previousSeason][level]['GS']

	playerInfo['Positions'] = {}
	positions = playerInfo['Positions']

	# computes the number of each type of appearance and enters information only if player had that type of appearance
	positions['P'] = {}
	positions['P']['G'] = games
	if tryFloat(starts) > 0:
		positions['SP'] = {}
		positions['SP']['G'] = starts
	if tryFloat(games) > int(starts):
		positions['RP'] = {}
		positions['RP']['G'] = str(tryFloat(games) - tryFloat(starts))

	# all stats that are needed for each pitcher entry
	# needed to make sure all needed elements of the XML are filled
	# pitcherStatList = ['BB', 'BS', 'Bk', 'CG', 'ER', 'G', 'GS', 'H', 'HB', 'HLD', 'HR', 'IBB', 'IP', 'InR', 'InS', 'L', 'QS', 'SH', 'SO', 'SV', 'W', 'WP']

	xml = updateXML(playerInfo, stats, xml)

	return xml


def hitterXML(playerInfo, stats, xml):
	'''Finds positions-specific information for each batter, cleans up the stats dictionary, and enters information in the XML.'''

	# print('Starting hitterXML')

	# determines the number of games played at each position from the player's last season (at the highest level they played at)
	# adds this information to playerInfo
	previousSeason = sorted(stats.keys())[-1]
	levels = sortLevels(stats[previousSeason])

	# removes the DH and turns LF/RF/CF into OF while keeping CF
	playerInfo['Positions'] = {}
	for level in levels:
		if 'Positions' in stats[previousSeason][level].keys():
			playerInfo['Positions'] = positionClean(stats[previousSeason][level]['Positions'])

	# enters errors into main stats dictionary and removes position information
	for year in sorted(stats.keys()):
		for level in sorted(stats[year].keys()):

			yearLevel = stats[year][level]
			positions = playerInfo['Positions']

			# initializes the error element for each year and level
			if 'E' not in yearLevel.keys():
				yearLevel['E'] = '0'

			# adds the total from each position played during that year and level to get the total errors
			for position in positions.keys():
				stats[year][level]['E'] = str(tryFloat(yearLevel['E']) + tryFloat(positions[position]['E']))

			# deletes all previous position information so I can iterate through without encountering a dictionary
			if 'Positions' in yearLevel.keys():
				del(stats[year][level]['Positions'])

	# print(str(stats))
	xml = updateXML(playerInfo, stats, xml)

	return xml


def sortLevels(stats):
	'''Returns a reverse sorted list of all levels that the player played in for the year.'''

	# print('Starting sortLevels')

	played = stats.keys()
	levels = ['NCAA', 'ind', 'Ind', 'Rk', 'A-', 'A', 'A+', 'AA', 'AAA', 'Intl', 'MLB']
	current = []

	# searches through each level in order and checks if the player played at that level that year
	for level in levels:
		if level in played:
			current.append(level)

	# errors out if no levels matched. they should always match
	# should I even return in this case?
	if not current:
		print('Did not find any acceptable playing level. Exiting.')
		sys.exit(1)

	return current


def positionClean(fielding):
	'''Cleans a dictionary of positions for a more fantasy-oriented experience.'''

	# print('Starting positionClean')

	# temporary dictionary to hold information while I iterate over the main dictionary
	newFielding = {}

	# if the TBC position is in positionDict, adds an entry for the fantasy position
	for position in fielding.keys():
		if position[-1] == 'F':
			
			# initializes the outfield position
			if 'OF' not in newFielding.keys():
				newFielding['OF'] = {}

			# only want to transfer over games played and errors made at the position
			for statName in ['E', 'G']:
				if statName not in newFielding['OF'].keys():
					newFielding['OF'][statName] = '0'

				# adds the number of games/errors to the entry listed
				statValue = newFielding['OF'][statName]
				statValue = str(tryFloat(statValue) + tryFloat(fielding[position][statName]))
				newFielding['OF'][statName] = statValue

	# gets rid of the non-fantasy positions
	for position in ['LF', 'RF', 'DH', 'P']:
		if position in fielding.keys():
			del(fielding[position])

	# adds any new positions that were created
	for position in newFielding.keys():
		if position not in fielding.keys():
			fielding[position] = {}
			fielding[position] = newFielding[position]

	if fielding == {}:
		fielding = {'U': {'G': '0', 'E': '0', 'Position': 'U'}}

	return fielding


def updateXML(playerInfo, stats, xml):
	'''Given all the stats and personal information, enters the information into the XML.'''

	# print('Starting updateXML')

	# creates the parent tag for the player, then adds it to the XML
	tag = xml.new_tag('Player', FullName=playerInfo['FullName'], PlayerID=playerInfo['PlayerID'], Birthday=playerInfo['Birthday'], Available=playerInfo['Available'])

	# creates the positions tag under the player tag and fills it with the position information
	positions = xml.new_tag('Positions')
	tag.append(positions)
	
	# for each position, enter it and the games played into the XML
	for position in sorted(playerInfo['Positions'].keys()):
		positionTag = xml.new_tag('Position', PositionName=position)
		positionTag.string = playerInfo['Positions'][position]['G']
		positions.append(positionTag)

	# all other stats are entered into the next section of XML
	for year in sorted(stats.keys()):
		for level in sorted(stats[year].keys()):

			seasonTag = xml.new_tag('Season', Year=year, Level=level)

			for statName in sorted(stats[year][level].keys()):
				statTag = xml.new_tag('Stat', StatName=statName)
				statTag.string = stats[year][level][statName]
				seasonTag.append(statTag)

			tag.append(seasonTag)

	xml.Players.append(tag)

	# print(xml.prettify())

	return xml


def tryFloat(string):
	'''Keeps the number as an int if it is an int, otherwise turns into a tryFloat.'''

	try:
		number = int(string)
	except:
		try:
			number = float(string)
		except:
			number = 0

	return number


def statVerify(stats, statList):
	'''Makes sure every value in statList has an entry in the stats dict.'''

	for year in stats.keys():
		for level in stats[year].keys():
			for statName in statList:
				if statName not in stats[year][level].keys():
					if statName == 'Positions':
						stats[year][level]['Positions'] = {'U': {'G': '0', 'E': '0', 'Position': 'U'}}
					else:
						stats[year][level][statName] = '0'

	return stats


def main():
	'''Parses command line arguments, the sends information to functions to scrape stats from the desired leagues.'''
	leagues = argParse(sys.argv[1:], [])
	for league in leagues:
		links = indexParse(league)
		profiles = letterParse(links, [])
		data = profileParse(profiles)

	for key in sorted(warningPlayers.keys()):
		print("Player {} (TBCID {}) was not entered into the database.".format(warningPlayers[key], key))

	return 0

if __name__ == '__main__':
	main()
