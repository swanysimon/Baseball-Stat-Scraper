#!/usr/bin/env python3.3

# Simon Swanson
# redditDynastyCalc.py
# takes in an XML file with player stats and finds the point totals for each player
# allows user to change availability of players

# horrible code, only for a quick calculator. please don't judge

from bs4 import BeautifulSoup
import re
import sys

# personal storage of some information
totalDict = {'3B': {'Raw': {'Mean': 200.0, 'StDev': 152.5, '30Mean': 369.0, '30StDev': 110.0}, 'Weighted': {'Mean': 273.0, 'StDev': 130.0, '30Mean': 404.0, '30StDev': 85.5}, 'ThreeYears': {'Mean': 230.5, 'StDev': 106.0, '30Mean': 338.0, '30StDev': 92.5}, 'Career': {'Mean': 230.0, 'StDev': 105.5, '30Mean': 341.0, '30StDev': 88.0}}, 'C': {'Raw': {'Mean': 129.5, 'StDev': 117.5, '30Mean': 269.0, '30StDev': 84.0}, 'Weighted': {'Mean': 236.5, 'StDev': 117.5, '30Mean': 361.0, '30StDev': 55.5}, 'ThreeYears': {'Mean': 179.0, 'StDev': 81.5, '30Mean': 266.5, '30StDev': 66.5}, 'Career': {'Mean': 182.0, 'StDev': 83.0, '30Mean': 272.5, '30StDev': 66.0}}, '1B': {'Raw': {'Mean': 251.5, 'StDev': 160.5, '30Mean': 430.5, '30StDev': 77.0}, 'Weighted': {'Mean': 307.5, 'StDev': 129.5, '30Mean': 436.5, '30StDev': 64.0}, 'ThreeYears': {'Mean': 272.0, 'StDev': 108.5, '30Mean': 388.0, '30StDev': 64.5}, 'Career': {'Mean': 274.5, 'StDev': 111.5, '30Mean': 397.5, '30StDev': 59.0}}, '2B': {'Raw': {'Mean': 192.0, 'StDev': 136.5, '30Mean': 345.5, '30StDev': 100.5}, 'Weighted': {'Mean': 269.0, 'StDev': 112.0, '30Mean': 393.5, '30StDev': 60.0}, 'ThreeYears': {'Mean': 226.5, 'StDev': 95.0, '30Mean': 331.5, '30StDev': 80.5}, 'Career': {'Mean': 226.0, 'StDev': 94.0, '30Mean': 330.5, '30StDev': 73.5}}, 'SS': {'Raw': {'Mean': 191.0, 'StDev': 131.5, '30Mean': 321.0, '30StDev': 76.0}, 'Weighted': {'Mean': 260.5, 'StDev': 121.5, '30Mean': 372.0, '30StDev': 73.5}, 'ThreeYears': {'Mean': 227.0, 'StDev': 100.0, '30Mean': 320.0, '30StDev': 73.0}, 'Career':  {'Mean': 224.0, 'StDev': 95.0, '30Mean': 314.5, '30StDev': 63.5}}, 'CF': {'Raw':  {'Mean': 203.0, 'StDev': 151.5, '30Mean': 390.0, '30StDev': 86.0}, 'Weighted': {'Mean': 279.0, 'StDev': 131.0, '30Mean': 424.0, '30StDev': 70.5}, 'ThreeYears': {'Mean': 239.0, 'StDev': 94.5, '30Mean': 347.0, '30StDev': 75.5}, 'Career': {'Mean': 235.5, 'StDev': 96.5, '30Mean': 348.0, '30StDev': 73.5}}, 'OF': {'Raw': {'Mean': 196.5, 'StDev': 152.0, '30Mean': 358.0, '30StDev': 89.5}, 'Weighted': {'Mean': 275.0, 'StDev': 135.5, '30Mean': 409.0, '30StDev': 66.0}, 'ThreeYears': {'Mean': 240.0, 'StDev': 104.5, '30Mean': 342.5, '30StDev': 81.0}, 'Career': {'Mean': 238.5, 'StDev': 103.0, '30Mean': 342.5, '30StDev': 73.0}}, 'RP': {'Raw': {'Mean': 125.5, 'StDev': 91.0, '30Mean': 244.5, '30StDev': 50.5}, 'Weighted': {'Mean': 130.5, 'StDev': 64.5, '30Mean': 208.5, '30StDev': 41.5}, 'ThreeYears': {'Mean': 122.0, 'StDev': 54.0, '30Mean': 190.0, '30StDev': 34.5}, 'Career': {'Mean': 122.5, 'StDev': 52.5, '30Mean': 190.5, '30StDev': 33.5}}, 'SP': {'Raw': {'Mean': 256.5, 'StDev': 152.5, '30Mean': 344.0, '30StDev': 111.0}, 'Weighted': {'Mean': 310.0, 'StDev': 153.5, '30Mean': 399.5, '30StDev': 101.0}, 'ThreeYears': {'Mean': 240.5, 'StDev': 123.5, '30Mean': 303.0, '30StDev': 107.5}, 'Career': {'Mean': 249.0, 'StDev': 116.0, '30Mean': 311.0, '30StDev': 95.5}}}

# dictionaries corresponding stats to points
hitterPoints = {'H': 1, '2B': 1, '3B': 2, 'HR': 3.5, 'BB': 1, 'HBP': 1, 'CS': -0.5, 'DP': -1, 'SO': -0.5, 'R': 1, 'RBI': 1, 'SB': 1.5, 'SF': 0.5, 'SH': 0.5, 'E': 0, 'IBB': 1, 'PA': 0, 'G': 0}
pitcherPoints = {'G': 0.5, 'Bk': -1, 'BB': -1, 'IBB': -0.5, 'WP': -0.5, 'ER': -2, 'H': -1, 'HB': -1, 'HR': -1, 'IP': 1, 'SO': 1, 'W': 3, 'L': -3, 'QS': 2, 'CG': 1, 'SH': 1, 'HLD': 2, 'SV': 3, 'BS': -1, 'GS': 0, 'InR': 0, 'InS': 0}
levelPoints = {'MLB': 1, 'Intl': 0.7, 'AAA': 0.8, 'AA': 0.6, 'A+': 0.3, 'A': 0.2, 'A-': 0.1, 'Rk': 0.05, 'NCAA': 0.1, 'ind': 0.1, 'Ind': 0.1}


def argParse(args, soup):
	# lookups loops through to find every possible match of the player, then prompts the user to enter the TBCID so I know for sure which player I'm getting
	if args[1] in ['--lookup', '-l']:
		# if the player's ID is known, just returns the player and some point information
		player = soup.find('Player', PlayerID=args[2])
		if player:
			players = pointEval([player], '-r')
			for player in players:
				printPretty(player)
		# if the player's name is known, searches for all possible players that match and then prompts the user to enter the player ID
		else:
			idnum = playerLookup(args[2:], soup)
			args = ['run', '-l', idnum]
			argParse(args, soup)
			sys.exit(1)

	# changes the player's availability attribute
	elif args[1] in ['--draft', '-d']:
		player = soup.find('Player', PlayerID=args[2])
		if player:
			availDict = {'Yes': 'No', 'No': 'Yes'}
			print("Changing {}'s availability from {} to {}.".format(player['FullName'], player['Available'], availDict[player['Available']]))
			player['Available'] = availDict[player['Available']]
			print('Successfully changed the availability of {}'.format(player['FullName']))
		else:
			idnum = playerLookup(args[2:], soup)
			args = ['run', '-d', idnum]
			argParse(args, soup)
			sys.exit(1)

	# ranks all players by the given method and given positions
	elif args[1] in ['--rank', '-r']:
		players = playerList(args[3:], soup)
		sortedPlayers = pointEval(players, args[2])
		for player in sortedPlayers:
			printPretty(player)
		if len(sortedPlayers) > 1:
			sdMean(sortedPlayers, args[2], 'all remaining')
		if len(sortedPlayers) > 10:
			sdMean(sortedPlayers[::-1][:10], args[2], 'top 10 remaining')

	elif args[1] in ['--finished', '-f']:
		output = open('All_Player_Information.xml', 'w')
		output.write(soup.prettify())
		output.close()


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
				try:
					statValue = int(stat.string.strip())
				except:
					value = float(stat.string.strip()) * 10
					statValue = int(value % 10) + 3 * int(value / 10)
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
		points[ID]['Weighted'] = round(points[ID]['Points'][-1][1] * 2) / 2
		longterm = 0
		for totals in points[ID]['Points']:
			longterm = (longterm + (totals[0] + totals[1]) / 2) / 2
		points[ID]['Long'] = round(longterm * 2) / 2
		totals = points[ID]['Points']
		if len(points[ID]['Points']) >= 3:
			miniTotal = (totals[-1][0] + totals[-1][1] + totals[-2][0] + totals[-2][1] + totals[-3][0] + totals[-3][1]) / 6.0
		elif len(points[ID]['Points']) == 2:
			miniTotal = (totals[-1][0] + totals[-1][1] + totals[-2][0] + totals[-2][1]) / 4.5
		else:
			miniTotal = (totals[-1][0] + totals[-1][1]) / 2.5
		threeyear = round(miniTotal * 2) / 2
		points[ID]['3Yr'] = threeyear

	if pointType in ['--weighted', '-w']:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['Weighted'])
	elif pointType in ['--threeyear', '-3']:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['3Yr'])
	elif pointType in ['--longterm', '-l']:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['Long'])		
	else:
		sortedPlayers = sorted(points.items(), key=lambda x:x[1]['Raw'])

	return sortedPlayers


def printPretty(player):
	# input is a tuple of the player's ID number and their information
	print('{}.\nPositions: {}. TBCID: {}.\n\tRaw total: {}.\tWeighted: {}.\n\t3 Year Average: {}.\tCareer: {}.'.format(player[1]['Name'], ', '.join(player[1]['Positions']), player[0], player[1]['Raw'], player[1]['Weighted'], player[1]['3Yr'], player[1]['Long']))
	return 0


def playerLookup(args, soup):
	# finds players based on given attributes
	i = []
	for arg in args:
		for player in soup.findAll('Player'):
			name = player['FullName']
			if arg in name:
				pid = player['PlayerID']
				s = soup.find('Player', PlayerID=pid, FullName=name)
				if s not in i:
					print('{}: {}.\n\tAvailable: {}. Birthday: {}.'.format(pid, name, player['Available'], player['Birthday']))
					i.append(s)
	if i == []:
		newName = input('Sorry, did not find any player matching that name. Please enter another name: ')
		idnum = playerLookup(newName.split(), soup)
		return idnum
	elif len(i) == 1:
		player = i[0]
		print('Processing TBCID {}. Name: {}'.format(player['PlayerID'], player['FullName']))
		return player['PlayerID']
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


def sdMean(players, arg, string):
	'''Finds SD and Mean for a list of players.'''

	if arg in ['--weighted', '-w']:
		mean = sum([p[1]['Weighted'] for p in players]) / float(len(players))
		var = sum([(p[1]['Weighted'] - mean) ** 2 for p in players]) / float(len(players))
	elif arg in ['--threeyear', '-3']:
		mean = sum([p[1]['3Yr'] for p in players]) / float(len(players))
		var = sum([(p[1]['3Yr'] - mean) ** 2 for p in players]) / float(len(players))
	elif arg in ['--longterm', '-l']:
		mean = sum([p[1]['Long'] for p in players]) / float(len(players))
		var = sum([(p[1]['Long'] - mean) ** 2 for p in players]) / float(len(players))
	else:
		mean = sum([p[1]['Raw'] for p in players]) / float(len(players))
		var = sum([(p[1]['Raw'] - mean) ** 2 for p in players]) / float(len(players))
	print('Mean of {} players: {}\nStandard Deviation of {} players: {}.'.format(string, str(round(mean * 2) / 2), string, str(round((var ** (0.5)) * 2) / 2)))
	return 0


def main():
	f = open('All_Player_Information.xml', 'r')
	soup = BeautifulSoup(f.read(), ['lxml', 'xml'])
	f.close()
	args = sys.argv
	argParse(args, soup)

	return 0

if __name__ == '__main__':
	main()