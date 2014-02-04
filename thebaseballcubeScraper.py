#!/usr/bin/env python3.3

# thebaseballcubeScraper.py
# Simon Swanson
# takes in stats from thebaseballcube.com and exports to an XML file for future use
#  plans for the future - updating of players as they get drafted/released from fantasy teams, updating stats, custom position eligibility, etc.


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
	
	# initializes the XML
	xml = BeautifulSoup(features='xml')
	xml.append(xml.new_tag('Players'))

	# updates the XML for each player
	# debate: when to write to file? I doubt my RAM can take everything
	for profile in profiles[:1]:
		soup = BeautifulSoup(get('http://thebaseballcube.com/players/{}'.format(profile.get('href'))).text)
		xml = playerInfo(xml, soup)

	return xml


def playerInfo(xml, soup):
	'''Finds all basic information on the player and adds it to an XML document.'''

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
		xml = batterXML(playerInfo, stats, xml)
	
	else:
		playerName = playerInfo['FullName']
		playerID = playerInfo['PlayerID']
		warningPlayers[playerID] = playerName
		print('{} caused a problem. Continuing.'.format(playerName))

	return xml


def personalInfo(soup):
	'''Finds all the basic personal information about the player as a dictionary.'''

	# stores in a dictionary
	info = {}
	info['FullName'] = infoSearch(soup, 'Full Name')
	info['PlayerID'] = infoSearch(soup, 'TBC Player ID')
	info['Birthday'] = infoSearch(soup, 'Born', 'a')
	# the available attribute is set to yes when the player is created
	# will come up with a way to modify the attribute as I figure out how to work this during the season
	info['Available'] = 'Yes'
	
	return info


def infoSearch(soup, match, subtag = None):
	'''Retrieves basic player information from the TBC header based on the string (and tag) given.'''

	# the information needed is in the div tag after the identifying div tag, as given by the matching string
	tag = soup.find('div', class_='cat1', text=match).findNextSibling('div')
	
	# for birthdays there is an a tag to go through before the string can be extracted
	if subtag:
		tag = tag.find(subtag)

	# after navigating to the correct location in the tree, extracts the string contained and cleans the whitespace
	info = tag.string.strip()

	return info


def pitcherParse(soup):
	'''Takes in a pitcher profile and adds the appropriate information to a dictionary.'''

	# lists of all the stats that come from the different sections
	basicList = ['BB', 'Bk', 'CG', 'ER', 'G', 'GS', 'H', 'HR', 'IP', 'L', 'Level', 'SH', 'SO', 'SV', 'W', 'WP', 'Year']
	advancedList = ['HB', 'Level', 'Year']
	extraList = ['BS', 'HLD', 'IBB', 'InR', 'InS', 'Level', 'QS', 'Year']

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

	return stats


def hitterParse(soup):
	'''Takes in a hitter profile and adds the appropriate information to a dictionary.'''

	# list of all the stats that come from the different sections
	hittingList = ['2B', '3B', 'BB', 'CS', 'DP', 'G', 'H', 'HBP', 'HR', 'IBB', 'Level', 'PA', 'R', 'RBI', 'SB', 'SF', 'SH', 'SO', 'Year']
	fieldingList = ['E', 'G', 'Level', 'Position', 'Year']

	# the first table will be hitting information
	hittingStats = tableTrim(soup.find('table', class_='stats'))

	# the fielding table is located as a sibling to the last div tag with the statsCategories1 class
	# the table is the next sibling table tag
	fielding = soup.find_all('div', class_='statsCategories1')[-1]
	fieldingStats = tableTrim(fielding.findNextSibling('table'))

	# stats are stored as a dictionary of years with subdictionaries by levels for easy access
	stats = {}
	stats = updateStats(hittingStats, hittingList, stats)
	stats = updateStats(fieldingStats, fieldingList, stats, fielding = True)

	return stats


def profileLink(soup, linkText, tagText):
	'''Retrieves the contents of a URL from a player profile based on the link URL and tag text'''

	# the separate pages of the player profile are in the href of an a tag 
	link = soup.find('a', href=re.compile(r'.+Page={}'.format(linkText)), text=tagText)['href']
	newSoup = BeautifulSoup(get('http://thebaseballcube.com/players/{}'.format(link)).text)

	return newSoup


def tableTrim(table):
	'''Cleans stat tables of all entries that are not regular season stats or the header.'''

	# the header is identified by headerRow should be the first entry in the table
	header = table.find('tr', class_='headerRow')

	# the summary stats are found under the footerRow or footerRowNotBold entry
	footer = table.find('tr', class_=re.compile(r'footerRow\w*'))

	# trims both ends of the table
	trimmedTable = table.find_all('tr')
	trimmedTable = trimmedTable[trimmedTable.index(header):]

	if footer in trimmedTable:
		trimmedTable = trimmedTable[:trimmedTable.index(footer)]

	return trimmedTable


def findIndices(header, items):
	'''Takes in the header of the table and matches the index of the stat in the header with the name of the stat.'''

	stats = {}
	# loops through all the elements in items to find the correct indices
	# assumes the all the elements exists (which I should have accounted for already)
	for item in items:
		index = header.index(item)
		stats[item] = index

	return stats


def updateStats(table, statList, stats, fielding = False):
	'''Using the indices given, extracts the appropriate stats from each year and puts them into a dictionary'''
	# sinfully long function

	# finds the indices for all the items in the list of needed statistics by comparing to the header section of the table
	indices = findIndices(table[0], statList)

	# for each part of the table (which is broken into unique teams per year) extracts all the necessary stats and updates the dictionary 
	for team in table[1:]:

		# extracts the year and the level from the information to use as identifying information
		# removes from the dictionary so I can loop through the rest of the dictionary extracting stats
		year = team[indices['Year']]
		level = team[indices['Level']]
		del(indices['Year'], indices['Level'])

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
			stats = updateFieldingStats(indices, stats, year, level)

		# goes through all stats in the dictionary and pulls out their value
		else:
			for statName in indices.keys():
				statValue = indices[statName]

				# if the stat is already entered for that year and level, adds the old number to the new number to find the total (possible because I have all counting stats)
				if statName in yearLevel.keys():
					oldValue = int(yearLevel[statName])
					# converts back to a string from an int for consistency and because XML takes strings
					statValue = str(oldValue + int(statValue))

				yearLevel[statName] = statValue

	print('Player has {} documented seasons.'.format(len(stats.keys())))
	return stats


def updateFieldingStats(indices, stats, year, level):
	'''Takes in fielding stats and adds to a dictionary or some shit'''

	# yearLevel should not need to be created because this function is only called after creation
	yearLevel = stats[year][level]

	# creates the positions subdictionary where information will be stored
	# the dictionary is named by the position name
	if 'Positions' not in yearLevel.keys():
		yearLevel['Positions'] = {}

	positions = yearLevel['Positions']
	positions[indices['Positions']] = {}

	if indicies['Positions'] not in positions.keys():
		fielding = positions[indicies['Positions']]
	
	del(indices['Position'])

	# loops through the other values and stores them under the position subdictionary
	for statName in indices.keys():
		statValue = indicies[statName]

		# in case the stats have already been entered (which I don't think is possible, but just in case)
		if statName in fielding.keys():
			oldValue = int(fielding[statName])
			# converts back to a string from an int for consistency and because XML takes strings
			statValue = str(oldValue + int(statValue))

		fielding[statName] = statValue

	return stats


def pitcherXML(playerInfo, stats, xml):
	'''Finds position-specific information for pitchers and sends the information to be entered in the XML.'''

	# determines the number of games for each type of pitching from last season (at the highest level the player played)
	# adds the information to playerInfo
	previousSeason = sorted(stats.keys())[-1]
	level = findHighestLevel(stats[previousSeason])
	games = stats[previousSeason][level]['G']
	starts = stats[previousSeason][level]['GS']

	playerInfo['Positions'] = {}
	positions = playerInfo['Positions']

	# computes the number of each type of appearance and enters information only if player had that type of appearance
	positions['P'] = games
	if starts > 0:
		positions['SP'] = starts
	if games > starts:
		positions['RP'] = str(int(games) - int(starts))

	# all stats that are needed for each pitcher entry
	# needed to make sure all needed elements of the XML are filled
	pitcherStatList = ['BB', 'BS', 'Bk', 'CG', 'ER', 'G', 'GS', 'H', 'HB', 'HLD', 'HR', 'IBB', 'IP', 'InR', 'InS', 'L', 'QS', 'SH', 'SO', 'SV', 'W', 'WP']

	xml = updateXML(playerInfo, stats, xml)

	return xml


def hitterXML(playerInfo, stats, xml):
	'''Finds positions-specific information for each batter, cleans up the stats dictionary, and enters information in the XML.'''

	# determines the number of games played at each position from the player's last season (at the highest level they played at)
	# adds this information to playerInfo
	previousSeason = sorted(stats.keys())[-1]
	level = findHighestLevel(stats[previousSeason])
	fielding = stats[previousSeason][level]['Positions']

	positions = {}
	played = fielding.keys()

	for position in played:
		positions[position] = fielding[positions]['G']

	# removes the DH and turns LF/RF/CF into OF while keeping CF
	playerInfo['Positions'] = {}
	playerInfo['Positions'] = positionClean(positions, stats[previousSeason][level])

	# enters errors into main stats dictionary and removes position information
	for year in stats.keys():
		for level in stats[year].keys():

			# initializes the error element for each year and level
			stats[year][level]['E'] = '0'
			errors = stats[year][level]['E']

			# adds the total from each position played during that year and level to get the total errors
			for position in stats[year][level]['Positions'].keys():
				errors = str(int(errors) + int(stats[year][level]['Positions'][position]['E']))

	# all stats needed for a hitter entry
	# needed to make sure that all needed elements are entered into the XML
	hitterStatList = []

	xml = updateXML(playerInfo, stats, xml)

	return xml


def highestLevel(stats):
	'''Returns the string of the highest level that the player played at in a year.'''

	played = stats.keys()
	levels = ['MLB', 'AAA', 'AA', 'A+', 'A', 'A-', 'Rk']

	# searches through each level in order and checks if the player played at that level that year
	for level in levels:
		if level in played:
			return level

	# errors out if no levels matched. they should always match
	print('Did not find any acceptable playing level. Exiting.')
	sys.exit(1)
	return 0


def positionClean(positions, yearStats):
	'''Cleans a dictionary of positions for a more fantasy-oriented experience.'''

	# dictionary relating values given by TBC and what fantasy baseball uses
	positionDict = {'LF': 'OF', 'CF': 'OF', 'RF': 'OF'}

	# if the TBC position is in positionDict, adds an entry for the fantasy position
	for position in positions.keys():
		if position in positionDict.keys():
			
			# newPosition is the fantasy name of the TBC position
			newPosition = positionDict[position]
			
			# initializes the 
			if newPosition not in positions.keys():
				positions[newPosition] = {}

			for statName in positions[position].keys():
				if statName not in positions[newPosition].keys():
					positions[newPosition][statName] = '0'

				# adds the number of games/errors to the entry listed
				positions[newPosition][statName] = str(int(positions[newPosition][statName]) + int(positions[position][statName]))

			if position != 'CF':
				del(positions[position])

	# gets rid of DH
	del(positions['DH'])

	return cleaned


def updateXML(playerInfo, stats, xml):
	'''Given all the stats and personal information, enters the information into the XML.'''

	# creates the parent tag for the player, then adds it to the XML
	tag = xml.new_tag('Player', FullName=playerInfo['FullName'], PlayerID=playerInfo['PlayerID'], Birthday=playerInfo['Birthday'], Available=playerInfo['Available'])
	xml.Players.append(tag)
	player = xml.Players.Player

	# creates the positions tag under the player tag and fills it with the position information
	positions = xml.new_tag('Positions')
	player.append(positions)
	
	# for each position, enter it into the XML
	for position in sorted(playerInfo['Positions'].keys()):
		positionTag = xml.new_tag(position)
		player.Positions.append(positionTag)
		positionTag.string = playerInfo['Positions']['G']

	for year in sorted(stat.keys()):
		for level in sorted(stat[year].keys()):

			seasonTag = xml.new_tag('Season', Year=year, Level=Level)

			for statName in sorted(stat[year][level].keys()):
				statTag = xml.new_tag(statName)
				player.Season.append(statTag)
				statTag.string = stat[year][level][statName]


	return xml


def main():
	'''Parses command line arguments, the sends information to functions to scrape stats from the desired leagues.'''
	leagues = argParse(sys.argv[1:], [])
	for league in leagues:
		links = indexParse(league)
		# currently just takes in all the "a" players
		profiles = letterParse(links[:1], [])
		data = profileParse(profiles)

	for key in sorted(warningPlayers.keys()):
		print("Player {} (TBCID {}) was not entered into the database.".format(warningPlayers[key], key))

	return

if __name__ == '__main__':
	main()
