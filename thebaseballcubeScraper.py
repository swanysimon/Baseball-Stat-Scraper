#!/usr/bin/env python3.3

# thebaseballcubeScraper.py
# Simon Swanson
# takes in stats from thebaseballcube.com and exports to an XML file for future use


from bs4 import BeautifulSoup
import re
from requests import get
import sys


def argParse(args, leagues):
	'''Takes in system args and turns them into a list of useable strings.'''

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
			print('ERROR: "' + arg + '" is not a valid argument.')
			print('\nValid arguments:')
			print('  "mlb" or "majors" for major league information')
			print('  "milb" or "minors" for minor league information')
			print('  "ncaa" or "college" for college player information')
			print('\n  EXAMPLE: "' + sys.argv[0] + ' minors ncaa" retrieves data on active players that have not made it to the major leagues and all current college players.')
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
		# currently only the > operator works because links for college are not working on the site right now
		links = soup.select('.otherPlayers > a[href^=' + league + ']')

	return links


def letterParse(links, profiles):
	'''Takes in a list of links to letters and opens them for each non-retired player.'''
	
	for link in links:
		soup = BeautifulSoup(get('mlb.asp?L=a').text)
		# soup = BeautifulSoup(get('http://www.thebaseballcube.com/players/' + link.get('href')).text)
		# all players are under the pre tag, active players are distinguished by including the b tag
		# retrieves all links that lead to an active player's profile
		for profile in soup.select('pre b a[href^="profile"]'):
			profiles.append(profile)

	return profiles


def profileParse(profiles):
	'''Takes in a list of links to profiles and write out all player information to file.'''

	return 0


def main():
	'''Parses command line arguments, the sends information to functions to scrape stats from the desired leagues.'''
	leagues = argParse(sys.argv[1:], [])
	for league in leagues:
		links = indexParse(league)
		profiles = letterParse(links, [])
	return 0

if __name__ == '__main__':
	main()