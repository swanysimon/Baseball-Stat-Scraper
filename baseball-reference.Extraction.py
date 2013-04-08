#!/usr/bin/python
# Simon Swanson
# baseball-reference.Extraction.py


import sys
import re
import urllib2
from string import lowercase
from bs4 import BeautifulSoup


# takes in a letter of the alphabet and passes that to a URL containing all baseball players whose last names starts with the given letter
def url_info(char):
    '''Opens the correct URLs then delegates work to other functions to get player information.'''
    req = urllib2.urlopen('http://www.baseball-reference.com/players/%s' % char)
    f = req.read()
    req.close()
    info_name = {}
    soup = BeautifulSoup(f, 'lxml')
    # lines with boldface are famous and/or active players
    boldface = soup.find_all('b')

    for line in boldface: 
        
        if line.find(text=re.compile(r'\s+\d+-201[12]')):
            link = line.a['href']

            if link:
                req = urllib2.urlopen('http://www.baseball-reference.com%s' % link)
                f = req.read()
                req.close()
                soup = BeautifulSoup(f, 'lxml')
                player = player_info(soup)
                player_name = player[0]
                
                # if the name already exists, add an underscore to the end of the name
                if player_name in info_name.keys():
                    player_name = player_name + '_'

                info_name[player_name] = (player[1], player[2], player[3])
                print player_name

    return info_name


def player_info(html):
    '''Gets the players name, age, postition eligibility, and statistics. Returns a tuple.'''
    # default values in case something goes wrong
    player_name = 'Unknown'
    age = None
    positions = []
    stats = []
    info_name = {}

    # gets fielding information only from 2012 to determine position eligibility (10+ games at the position previous year)
    fielding = html.find_all(onclick='sumSpan(this);', id='2012:standard_fielding')

    for lines in fielding:
        games = lines.find_all('td', align='right')
        line = lines.find_all('td', align='left')
        # age can also be found in this fielding section. problematic if player didn't play in 2012, so I have a more complicated check below
        age = int(games[0].string)

        if int(games[1].string) >= 10:
            positions.append(str(line[3].string))

    # for cases where the player didn't play the field and/or doesn't have a position from 2012, I refer to baseball-reference.com's position (which is wrong in several cases, but at least gives me something to work with)
    if not positions:
        get_line = re.search(r'Positions?</strong>:([\w, ]+)\n', str(html))
        positions = position_info(get_line.group(1))
    
    # from the position I can find the appropriate stats (because there are no pitcher/fielders in the game today except in 20-0 blowouts)
    if positions[0] == 'P':
        stats = pitcher_info(html)
    else:
        stats = batter_info(html)

    # player's name is in the first h1 tag
    player_name = html.h1.string

    # verifies that the player has an age
    if not age:
        tag = html.find('span', id='necro-birth')
        dob = tag['data-birth']
        age = 2013 - int(dob[:4])

    return (player_name, age, positions, stats)


# simple extraction of batting stats (24 per year), puts into list
def batter_info(html):
    '''Gets all batter stats.'''
    batting_stats = []
    hitting = html.find_all('tr', class_='full', id=re.compile(r'batting_standard\.\d+'))
    
    if not hitting:
        batting_stats = pitching_stats(html)

    # excludes first element of the list because it's the player's age for each year (which I have more efficienty ways of getting)
    for lines in hitting:
        stats = lines.find_all('td', align='right')[1:]

        for stat in stats:
            stat = stat.string

            # sometimes there isn't a stat for something, and baseball-reference just leaves it blank
            if not stat:
                stat = 0

            batting_stats.append(float(stat))

    return batting_stats


# simple extraction of pitching stats (29 per year). Pitchers are more likely to succumb to the None value in their stats (more ratios) and can even have inf ratio values
def pitcher_info(html):
    '''Gets all statistics for pitchers.'''
    pitching_stats = []
    pitching = html.find_all('tr', class_='full', id=re.compile(r'pitching_standard\.\d+'))

    if not pitching:
        return ['0']

    for lines in pitching:
        stats = lines.find_all('td', align='right')[1:]

        for stat in stats:
            stat = stat.string
            
            if not stat:
                stat = 0

            # it is possible to have a pitcher stat be divided by 0 in some extreme cases. 1000 seems like a punishable enough number to work with
            if stat == 'inf':
                stat = 1000
                
            pitching_stats.append(float(stat))

    return pitching_stats


# figures out what's in the baseball-reference.com position list
def position_info(pos):
    '''If the position was not available before, matches with positions listed at the top of the page.'''
    positions = []
    position_dict = {'Pitcher': 'P', 'Catcher': 'C', 'First Baseman': '1B', 'Second Baseman': '2B', 'Third Baseman': '3B', 'Shortstop': 'SS', 'Outfielder': 'OF', 'Leftfielder': 'LF', 'Centerfielder': 'CF', 'Rightfielder': 'RF', 'Designated Hitter': 'DH'}

    # loops through the dict to try and match the key with the string of positions
    for key in position_dict:

        if key in pos:
            positions.append(position_dict[key])

    # some people just don't have a real position (pinch runner, etc.) and get the unknown label
    if not positions:
        return ['Unknown']

    return positions


# passes each letter of the alphabet to url_info
def main():
    '''Gets the information from every active major league baseball player, returned as a dictionary to a file.'''
    args = lowercase
    output = open('/Users/Swanson/Programs/Python/All_Player_Information.txt', 'w')
    info = []
    s = ''

    # adds all the separate dictionaries to a list as strings for further use
    for arg in args:
        info.append(str(url_info(arg)))
        print 'Finished with letter %s!\n' % arg

    # makes it all one big string to operate on
    for players in info:
        s += players

    # replaces all the dictionary separators to make one large dictionary
    s = s.replace('(}{)+', ', ')
    output.write(s)
    output.close()


if __name__ == '__main__':
    main()
