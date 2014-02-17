#!/usr/bin/env python3.3

# Simon Swanson
# redditDynastyCalc.py
# takes in an XML file with player stats and finds the point totals for each player
# allows user to change availability of players

from bs4 import BeautifulSoup
import re
import sys





def argParse(args, soup):
	# lookups loops through to find every possible match of the player, then prompts the user to enter the TBCID so I know for sure which player I'm getting
	if args[0] in ['--lookup', '-l']:
		# if the player's ID is known, just returns the player and some point information
		try:
			int(args[1])
			player = soup.find('Player', PlayerID=args[1])
		# if the player's name is known, searches for all possible players that match and then prompts the user to enter the player ID
		except:
			idnum = playerLookup(args[1:], soup)
			argParse(['-l', idnum], soup)

	if args[0] in ['--draft', '-d']:
		try:
			int(args[1])
			player = soup.find('Player', PlayerID=args[1])
			availDict = {'Yes': 'No', 'No': 'Yes'}
			confirm = input("Would you like to change {}'s availability from {} to {}? (y/n) ".format(player['FullName'], player['Availability'], availDict[player['Availability']]))
			if confirm == 'y':
				player['Available'] = availDict[player['Available']]
				output = open('All_Player_Information.xml', 'w')
				output.write(soup)
				output.close()
				print('Successfully changed the availability of {}'.format(player['FullName']))
				sys.exit(1)
			else:
				print('Exiting.')
				sys.exit(1)
		except:
			idnum = playerLookup(args[1:], soup)
			argParse(['-d', idnum], soup)

		return 0


def playerLookup(args, soup):
	i = 0
	for arg in args:
		for player in soup.findAll('Player'):
			name = player['FullName']
			if arg in player['FullName']
				print('ID: {}. Player Name: {}. Available: {}. Birthday: {}.'.format(player['PlayerID'], player['FullName'], player['Available'], player['Birthday']))
					i += 1
	if i == 0:
		print('Sorry, did not find any player matching that name.')
		sys.exit(1)
	else:
		idnum = input('Please enter the player ID: ')
		return idnum


def main():
	f = open('All_Player_Information.xml', 'r')
	soup = BeautifulSoup(f.read(), ['lxml', 'xml'])
	f.close()
	args = sys.argv[1:]
	argParse(args, soup)
	f.close()

	return 0

if __name__ == '__main__':
	main()