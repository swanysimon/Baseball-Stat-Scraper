#!/usr/bin/env python3.3

# Simon Swanson
# redditDynastyCalc.py
# takes in an XML file with player stats and finds the point totals for each player
# allows user to change availability of players

# horrible code, only for a quick calculator. please don't judge

from bs4 import BeautifulSoup
import re
import sys

# dictionaries corresponding stats to points
hitterPoints = {'H': 1, '2B': 1, '3B': 2, 'HR': 3.5, 'BB': 1, 'HBP': 1, 'CS': -0.5, 'DP': -1, 'SO': -0.5, 'R': 1, 'RBI': 1, 'SB': 1.5, 'SF': 0.5, 'SH': 0.5, 'E': 0, 'IBB': 1, 'PA': 0, 'G': 0}
pitcherPoints = {'G': 0.5, 'Bk': -1, 'BB': -1, 'IBB': -0.5, 'WP': -0.5, 'ER': -2, 'H': -1, 'HB': -1, 'HR': -1, 'IP': 3, 'SO': 1, 'W': 3, 'L': -3, 'QS': 2, 'CG': 1, 'SH': 1, 'HLD': 2, 'SV': 3, 'BS': -1, 'GS': 0, 'InR': 0, 'InS': 0}
levelPoints = {'MLB': 1, 'Intl': 0.7, 'AAA': 0.8, 'AA': 0.6, 'A+': 0.3, 'A': 0.2, 'A-': 0.1, 'Rk': 0.05, 'NCAA': 0.1, 'ind': 0.1, 'Ind': 0.1}


def argParse(args, soup):
	# lookups loops through to find every possible match of the player, then prompts the user to enter the TBCID so I know for sure which player I'm getting
	if args[1] in ['--lookup', '-l']:
		# if the player's ID is known, just returns the player and some point information
		try:
			int(args[3])
			player = soup.find('Player', PlayerID=args[3])
			pointEval([player], args[2])
		# if the player's name is known, searches for all possible players that match and then prompts the user to enter the player ID
		except:
			idnum = playerLookup(args[3:], soup)
			argParse(['-l', '-r', idnum], soup)

	# changes the player's availability attribute
	elif args[1] in ['--draft', '-d']:
		try:
			int(args[2])
			player = soup.find('Player', PlayerID=args[2])
			availDict = {'Yes': 'No', 'No': 'Yes'}
			confirm = input("Would you like to change {}'s availability from {} to {}? (y/n) ".format(player['FullName'], player['Availability'], availDict[player['Availability']]))
			if confirm == 'y':
				player['Available'] = availDict[player['Available']]
				output = open('All_Player_Information.xml', 'w')
				output.write(soup)
				output.close()
				print('Successfully changed the availability of {}'.format(player['FullName']))
		except:
			idnum = playerLookup(args[2:], soup)
			argParse(['-d', idnum], soup)

	# ranks all players by the given method and given positions
	elif args[1] in ['--rank', '-r']:
		players = playerList(args[3:], soup)
		pointEval(players, args[2])

	question = input('Do you have more to process? (y/n) ')
	if question == 'y':
		newArgs = input('\nPlease enter your new command here (and please include the program name):\n$ ')
		argParse(newArgs.split(), soup)
	else:
		print('Exiting.')

		return 0


def pointEval(players, pointType):
	# takes a list of players, evaluates their points, and returns them in a sorted order
	points = {}
	for player in players:
		positions = positionFind(player)
		ID = player['PlayerID']
		points[ID] = {'Name': player['FullName'], 'Positions': positions, 'Year': 0, 'Level': 'Rk', 'Weighted': 0, 'Raw': 0, '3Yr': 0, 'Long': 0, 'Points': [], 'Games': 0, 'TempPoints': 0}
		seasons = player.findAll('Season')
		# print('Working on {}, {}'.format(player['FullName'], str(positions)))
		for season in seasons:
			year = int(season['Year'])
			level = season['Level']
			try:
				games = int(season.find('Stat', StatName='G').string.strip())
			except:
				games = 0
			stats = season.findAll('Stat')
			totalValue = 0
			for stat in stats:
				statName = stat['StatName']
				statValue = int(float(stat.string.strip()))
				if 'U' in positions:
					if statName in hitterPoints.keys():
						totalValue += statValue * hitterPoints[statName] * levelPoints[level]
				else:
					if statName in pitcherPoints.keys():
						totalValue += statValue * pitcherPoints[statName] * levelPoints[level]
			totalValue += points[ID]['TempPoints']
			games += points[ID]['Games']
			if points[ID]['Year'] != year:
				# because of the way I bring players around I can guarantee games will not be 0
				if 'U' in positions:
					exportTuple = (totalValue, totalValue * 150.0 / games)
				elif 'SP' in positions:
					exportTuple = (totalValue, totalValue * 33.0 / games)
				elif 'RP' in positions:
					exportTuple = (totalValue, totalValue * 50.0 / games)
				else:
					exportTuple = (totalValue, totalValue * 35.0 / games)
				points[ID]['Points'].append(exportTuple)
				points[ID]['TempPoints'] = 0
				points[ID]['Games'] = 0
		points[ID]['Raw'] = points[ID]['Points'][-1][0]
		points[ID]['Weighted'] = round(points[ID]['Points'][-1][1] * 2, 1) / 2
		longterm = 0
		for totals in points[ID]['Points']:
			longterm = (longterm + (totals[0] + totals[1]) / 2) / 2
		points[ID]['Long'] = round(longterm * 2, 1) / 2
		totals = points[ID]['Points']
		if len(points[ID]['Points']) >= 3:
			miniTotal = (totals[-1][0] + totals[-1][1] + totals[-2][0] + totals[-2][1] + totals[-3][0] + totals[-3][1]) / 6.0
		elif len(points[ID]['Points']) == 2:
			miniTotal = (totals[-1][0] + totals[-1][1] + totals[-2][0] + totals[-2][1]) / 4.5
			threeyear = rou
		else:
			miniTotal = (totals[-1][0] + totals[-1][1]) / 2.5
		threeyear = round(miniTotal * 2, 1) / 2
		points[ID]['3Yr'] = threeyear

	if pointType in ['--weighted', '-w']:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['Weighted'])
	elif pointType in ['--threeyear', '-3']:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['3Yr'])
	elif pointType in ['--longterm', '-l']:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['Long'])		
	else:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['Raw'])
	for player in sortedPlayers:
		printPretty(player)
	return 0


def printPretty(player):
	# input is a tuple of the player's ID number and their information
	print('{}.\nPositions: {}. TBCID: {}.\n\tRaw total: {}.\tWeighted: {}.\n\t3 Year Average: {}.\tCareer: {}.'.format(player[1]['Name'], ', '.join(player[1]['Positions']), player[0], player[1]['Raw'], player[1]['Weighted'], player[1]['3Yr'], player[1]['Long']))
	return 0


def playerLookup(args, soup):
	# finds players based on given attributes
	i = 0
	for arg in args:
		for player in soup.findAll('Player'):
			name = player['FullName']
			if arg in player['FullName']:
				print('ID: {}. Player Name: {}. Available: {}. Birthday: {}.'.format(player['PlayerID'], player['FullName'], player['Available'], player['Birthday']))
				i += 1
	if i == 0:
		print('Sorry, did not find any player matching that name.')
		sys.exit(1)
	else:
		idnum = input('Please enter the player ID: ')
		return idnum


def playerList(positions, soup):
	# comes up with a list of players meeting a certain criteria
	players = []
	available = soup.findAll('Player', Available='Yes')
	if 'U' in positions or 'P' in positions:
		if 'U' in positions:
			for player in available:
				if player.findAll('Position', Position=lambda x:x not in ['P', 'RP', 'SP']):
					players.append(player)
		if 'P' in positions:
			for player in available:
				if player not in players:
					if player.findAll('Position', Position=lambda x:x in ['P', 'RP', 'SP']):
						players.append(player)
	else:
		for player in available:
			if player not in players:
				if player.findAll('Position', PositionName=lambda x:x in positions, text=lambda y:int(y.strip()) >= 10):
					players.append(player)
	return players


def positionFind(player):
	# finds the positions that the player qualifies at
	positions = []
	for positionTag in player.findAll('Position', text=lambda y:int(y.strip()) >= 10):
		positions.append(positionTag['PositionName'])
	for positionTag in player.findAll('Position'):
		if 'U' in positionTag['PositionName'] and 'U' not in positions:
			positions.append('U')
		if 'P' in positionTag['PositionName'] and 'P' not in positions:
			positions.append('P')
	return positions


def main():
	f = open('All_Player_Information.xml', 'r')
	soup = BeautifulSoup(f.read(), ['lxml', 'xml'])
	f.close()
	args = sys.argv
	argParse(args, soup)

	return 0

if __name__ == '__main__':
	main()