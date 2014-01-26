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
	else if 'BATTING' in mainPosition:
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
	basicList = ['Year', 'Level', 'G', 'GS', 'IP', 'ER', 'W', 'L', 'SV', 'CG', 'SH', 'H', 'HR', 'BB', 'SO', 'Bk', 'WP']
	advancedList = ['Year', 'Level', 'HB']
	extraList = ['Year', 'Level', 'BS', 'HLD', 'QS', 'IBB', 'InR', 'InS']

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
	hittingList = ['Year', 'Level', 'G', 'PA', 'H', '2B', '3B', 'HR', 'BB', 'IBB', 'HBP', 'SB', 'CS', 'DP', 'SO', 'R', 'RBI', 'SF', 'SH']
	fieldingList = ['Year', 'Level', 'Position', 'G', 'E']

	# the first table will be hitting information
	hittingStats = tableTrim(soup.find('table', class_='stats'))

	# the fielding table is located as a sibling to the last div tag with the statsCategories1 class
	# the table is the next sibling table tag
	fielding = soup.find_all('div', class_'statsCategories1')[-1]
	fieldingStats = tableTrim(fielding.findNextSibling('table'))

	# stats are stored as a dictionary of years with subdictionaries by levels for easy access
	stats = {}
	stats = updateStats(hittingStats, hittingList, stats)
	stats = updateStats(fieldingStats, fieldingList, stats, fielding = True)

	return stats


def positionParse(soup):
	'''Returns all positions that the player played the previous year and the number of games played at those positions in a dictionary.'''

	return positions


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
		else if level not in stats[year].keys():
			stats[year][level] = {}
		
		# fielding gets it's own subdictionary to avoid name conflict with the other stat categories
		if fielding:
			for statName in indices.keys():
				statValue = indices[statName]

		else:
			# goes through all stats in the dictionary and pulls out their value
			for statName in indices.keys():
				statValue = indices[statName]

				# if the stat is already entered for that year and level, adds the old number to the new number to find the total (possible because I have all counting stats)
				if statName in stats[year][level].keys():
					oldValue = int(stats[year][level][statName])
					# converts back to a string from an int for consistency and because XML takes strings
					statValue = str(oldValue + int(statValue))

				stats[year][level][statName] = statValue

	print('Player has {} documented seasons.'.format(len(stats.keys())))
	return stats


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
