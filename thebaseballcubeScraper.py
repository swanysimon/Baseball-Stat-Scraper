#!/usr/bin/env python3.3

# thebaseballcubeScraper.py
# Simon Swanson
# takes in stats from thebaseballcube.com and exports to an XML file for future use


from bs4 import BeautifulSoup, Comment
import re
from requests import get
import sys


# players that throw an error are saved in a dictionary to be spit out later
warningPlayers = {}


def argParse(args, leagues):
	'''Takes in system args and turns them into a list of useable strings or errors out.'''

	# default value with no arguments is to scrape mlb player data
	if not args:
		return ['mlb']

	leagueDict = {'majors': 'mlb', 'milb': 'minors', 'ncaa': 'college'}
	# loops through all arguments to find which leagues should be looked at
	for arg in args:
		if arg in leagueDict.values():
			leagues.append(arg)
		elif arg in leagueDict.keys():
			leagues.append(leagueDict[arg])
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
	'''Opens the index URL and finds the correct links to follow based on the leagues given.'''
	
	soup = BeautifulSoup(get('http://www.thebaseballcube.com/players/').text)
	# mlb players are under the div.letters tag, minors and college players are under the div.otherPlayers tag
	# retrieves all links that lead to an index of last names
	if league == 'mlb':
		links = soup.select('.letters a[href^="mlb"]')
	else:
		# currently the > operator works because links for college are not working on the site right now
		links = soup.select('.otherPlayers > a[href^={}]'.format(league))

	return links


def letterParse(links, profiles):
	'''Takes in a list of links to letters and opens them for each non-retired player.'''
	
	for link in links:
		# soup = BeautifulSoup(get('mlb.asp?L=a').text)
		soup = BeautifulSoup(get('http://www.thebaseballcube.com/players/{}'.format(link.get('href'))).text)
		# all players are under the pre tag, active players are distinguished by including the b tag
		# retrieves all links that lead to an active player's profile
		profiles.append(profile) for profile in soup.select('pre b a[href^="profile"]'):

	return profiles


def profileParse(profiles):
	'''Takes in a list of links to profiles and turns all needed information to an XML format.'''
	
	# initializes the XML
	xml = BeautifulSoup(features='xml')
	xml.append(xml.new_tag('players'))

	# updates the XML for each player
	for profile in profiles[:1]:
		soup = BeautifulSoup(get('http://thebaseballcube.com/players/{}'.format(profile.get('href'))).text)
		xml = playerInfo(xml, soup)

	return xml


def playerInfo(xml, soup):
	'''Finds all basic information on the player and adds it to an XML document.'''

	# finds the playe's personal information that will be used to identiy then later on
	personalInfo = {}
	personalInfo['FullName'] = infoSearch(soup, 'Full Name')
	personalInfo['PlayerID'] = infoSearch(soup, 'TBC Player ID')
	personalInfo['Birthday'] = infoSearch(soup, 'Born', 'a')
	# the available attribute is set to yes when the player is created, will come up with a way to modify the attribute as I figure out how to work this during the season
	personalInfo['Available'] = 'Yes'

	# the player's stats for his main position is in the first statsCategories1 div tag
	# the string in the statsCategories1 div tag shows whether the player is primarily a pitcher or batter
	mainPosition = soup.find('div', class_='statsCategories1').string

	# if the player is a pitcher or batter, retrieves the correct stats and updates the xml
	# otherwise throws a warning, stores the player's name and ID, and continues
	if 'PITCHING' in mainPosition:
		stats = pitcherParse(soup)
		xml = pitcherXML(personalInfo, stats, xml)
	
	else if 'BATTING' in mainPosition:
		stats = hitterParse(soup)
		xml = batterParse(personalInfo, stats, xml)
	
	else:
		playerName = personalInfo['FullName']
		playerID = personalInfo['PlayerID']
		warningPlayers[playerID] = playerName
		print('{} caused a problem. Continuing.'.format(playerName))

	return xml


def infoSearch(soup, match, subtag = ''):
	'''Retrieves basic player information from the TBC header based on the string (and tag) given.'''

	# the information needed is in the div tag after the identifying div tag, as given by the matching string
	tag = soup.find('div', class_='cat1', text=match).findNextSibling('div')
	
	# for birthdays there is an a tag to go through before the string can be extracted
	if subtag:
		tag = tag.find(subtag)

	# after navigating to the correct location in the tree, extracts the string contained
	info = tag.string.strip()

	return info


def pitcherParse(soup):
	'''Takes in a pitcher profile and adds the appropriate information to a dictionary.'''


	mainStats = soup.find('div', class_='statsCategories1').find_next('table')
	extraStatLink = soup.find('a', href=re.compile(r'.+Page=ExtraP'), text='Extra')['href']
	stats = {}

	return stats


def hitterParse(soup):
	positions = positionParse(xml, soup)
	'''Takes in a hitter profile and adds the appropriate information to a dictionary.'''
	return 0


def positionParse(soup):
	'''Returns all positions that the player played the previous year and the number of games played at those positions in a dictionary.'''
	positions = {}
	return positions



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

if __name__ == '__main__':
	main()/