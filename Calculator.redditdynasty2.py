#!/usr/bin/python
# Simon Swanson
# Calculator.redditdynasty2.py

import sys
import ast
import math


# takes in a player's information and sifts through it to get things I need
def player_stats(tup):
    '''Gets the raw ranked stats of each player, unsorted by position.'''
    points = []
    positions = tup[1]
    stats = tup[2]

    if positions[0] == 'P':
        points = pitcher_stats(stats)
    else:
        points = batter_stats(stats)

    # gets the 3 year average of weighted and non-weighted performance
    if len(points) == 6:
        point_sum = sum(points[:6]) / 6
    elif len(points) == 4:
        point_sum = sum(points) / 4
    else:
        point_sum = sum(points) / 2

    return (tup[0], positions, [points[1], points[0], point_sum])


def pitcher_stats(stats):
    '''Pitcher stats are fairly accurate due to IP+K being teh bulk of points earned.'''
    points = []
    
    # very adjusted stats, but roughly on the same level as with batters. no site has every stat I need, unfortunately
    while stats:
        total = 1.1 * ((stats[-20] + stats[-29]) * 3 + stats[-8] + stats[-12] + stats[-25] * .5 - stats[-9] - (stats[-15] + stats[-11] + stats[-14] + stats[-16] + stats[-18]) * 2 - stats[-28] * 3)

        if stats[-19] / stats[-25] > 4:
            weighted = 30 / (stats[-25] + 1) * total
        else:
            weighted = 60 / (stats[-19] + 1) * total
        
        stats = stats[:-29]
        points.append(int(weighted))
        points.append(int(total))

    return points[:6]


def batter_stats(stats):
    '''Because I don't count errors there are some complications, but they're fairly accurate overall.'''
    points = []
    
    # every stat scored in redditdynasty2. I count K's as extra but give the IBB + BB total, also don't count errors
    # repeats over every year: points/150 games and total points
    while stats:
        total = stats[-13] + stats[-2] + stats[-3] + stats[-15] * 1.5 + stats[-16] + stats[-21] + stats[-17] * .5 + stats[-6] - stats[-12] * .5 - stats[-5] - stats[-14] * .5
        weighted = 150 / (stats[-24] + 1) * total
        points.append(int(weighted))
        points.append(int(total))
        stats = stats[:-24]

    return points[:6]


# filters through every position and sticks the correct people into the correct pile
def position_sort(p, c, one, two, three, ss, of, cf, u, f):
    '''Sorts all players into their positions for easy viewing.'''
    for line in f.readlines():
        line = ast.literal_eval(line)
        i = 0

        for key in line.keys():
            pos = line[key][1]

        if pos[0] == 'P':
            p.write(str(line) + '\n')
            i += 1
        
        for position in pos:

            if position.endswith('C'):
                c.write(str(line) + '\n')
                i += 1
            if position.startswith('1B'):
                one.write(str(line) + '\n')
                i += 1
            if position.startswith('2B'):
                two.write(str(line) + '\n')
                i += 1
            if position.startswith('3B'):
                three.write(str(line) + '\n')
                i += 1
            if position.startswith('SS'):
                ss.write(str(line) + '\n')
                i += 1
            if position.startswith('CF'):
                cf.write(str(line) + '\n')
                i += 1
            if position.startswith('OF'):
                of.write(str(line) + '\n')
                i += 1
            if position.startswith('D') or i == 0:
                u.write(str(line) + '\n')
    
    return "Sort successful!"


def main():
    '''Takes in player information from All_Player_Information.txt and outputs a ranked list of positions players for each position.'''
    f = open('/Users/Swanson/Programs/Python/All_Player_Information.txt', 'rU')
    lines = f.read()
    line = ast.literal_eval(lines)
    path = '/Users/Swanson/Programs/Python/redditdynasty2/'
    names = ['0Total_', '1Weighed_', '2Three_Years_']

    for string in names:
        raw = open('%s%sRaw.txt' % (path, string[1:]), 'w')
        player_dict = {}

        for key in line:
            info = player_stats(line[key])
            player_dict[key] = info

        for player in sorted(player_dict.items(), key = lambda x: x[1][2][int(string[0])], reverse=True):
            quick_dict = {}
            quick_dict[player[0]] = player[1]
            raw.write(str(quick_dict) + '\n')

        f.close()
        raw.close()
        pitcher = open('%s%sPitcher.txt' % (path, string[1:]), 'w')
        catcher = open('%s%sCatcher.txt' % (path, string[1:]), 'w')
        first = open('%s%sFirst.txt' % (path, string[1:]), 'w')
        second = open('%s%sSecond.txt' % (path, string[1:]), 'w')
        third = open('%s%sThird.txt' % (path, string[1:]), 'w')
        short = open('%s%sShort.txt' % (path, string[1:]), 'w')
        outfield = open('%s%sOutfield.txt' % (path, string[1:]), 'w')
        center = open('%s%sCenter.txt' % (path, string[1:]), 'w')
        unknown = open('%s%sOther.txt' % (path, string[1:]), 'w')
        raw = open('%s%sRaw.txt' % (path, string[1:]), 'rU')
        positions = position_sort(pitcher, catcher, first, second, third, short, outfield, center, unknown, raw)
        print positions
        pitcher.close()
        catcher.close()
        first.close()
        second.close()
        third.close()
        short.close()
        outfield.close()
        center.close()
        unknown.close()
        print 'Done!'


if __name__ == '__main__':
    main()
