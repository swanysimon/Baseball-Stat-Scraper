#!/usr/bin/env python3


"""statScraper.py: scrapes baseball-reference.com for a large number of statistics and stores them in a database for local use"""

__author__      = "Simon Swanson"
__copyright__   = "Copyright 2015, Simon Swanson"
__license__     = "GPL"
__version__     = "1.0.0"
__maintainer__  = "Simon Swanson"


import argparse
from bs4 import BeautifulSoup
from Player import Player
import re
import requests
from SQLController import SQLController
import sys


def iint(string):
    try:
        return int(string.strip())
    except:
        return 0


def ffloat(string):
    try:
        return float(string.strip())
    except:
        return 0


def parsePlayerProfile(path, args):
    soup = BeautifulSoup(requests.get("{domain}/{pathStr}".format(domain=args.domain[0], pathStr=path)).text, "html.parser")

    playerPathName  = re.split("/|\.", path.lower())[-2]
    # set up so a=11, b=12, etc, then joins the values together
    playerID        = "".join([char if char.isdigit() else str(ord(char) % 86) for char in playerPathName])
    birthday        = soup.find("span", id="necro-birth").get("data-birth")
    primaryPosition = soup.find("strong", string=re.compile(r"^Position")).find_next_sibling("span").string
    retired         = bool(soup.find("a", string="Last Game"))

    player = parseProfileHeader(soup, playerID, birthday, retired, args)

    positionTable = soup.find("table", id="standard_fielding")
    positions     = parsePositionInfo(positionTable, primaryPosition, args)
    player.addPositions(positions)

    hittingTable = soup.find("table", id="batting_standard")
    hittingStats = parseBattingTable(hittingTable, args)
    player.addStats(hittingStats, "batting")

    pitchingTable   = soup.find("table", id="pitching_standard")
    advancedPathTag = soup.find("a", href=re.compile(r"-pitch.shtml"), string="More Stats")
    pitchingStats   = parsePitchingTables(pitchingTable, advancedPathTag, args)
    player.addStats(pitchingStats, "pitching")

    return player


def parseProfileHeader(soup, playerID, birthday, retired, args):
    nameTag      = soup.find("span", id="player_name")
    rosterName   = nameTag.string.strip()
    fullName     = nameTag.find_parent("div").find_next_sibling("p").strong.string.strip()
    player       = Player(playerID, fullName, rosterName, birthday, retired)
    playerString = "Made player profile for {player}".format(player=player) if args.verbose else "Starting processing {name}".format(name=rosterName)
    print(playerString)

    return player


def parsePositionInfo(fieldingTable, primaryPosition, args):
    if not fieldingTable: return {}
    fieldingStats = {}
    fieldingTable = fieldingTable.tbody.find_all("tr", class_=re.compile(r"full"))

    if args.verbose: print("Processing {season} seasons of major league fielding stats".format(season=len(fieldingTable)))

    if fieldingTable:
        for row in fieldingTable:
            seasonStats = {}
            stats       = row.find_all("td")

            seasonStats["year"]     = iint(stats[0].find(string=True))
            seasonStats["age"]      = iint(stats[3].find(string=True))
            seasonStats["level"]    = "mlb"
            seasonStats["position"] = stats[4].string.strip()
            seasonStats["games"]    = iint(stats[5].find(string=True))

            year  = seasonStats["year"]
            level = seasonStats["level"]

            fieldingStats[year]        = {}
            fieldingStats[year][level] = seasonStats

            if args.verbose: print("Processed position {season}")


    positionDict = {
            "Pitcher":        ["P"],
            "Catcher":        ["C"],
            "First Baseman":  ["1B"],
            "Second Baseman": ["2B"],
            "Third Baseman":  ["3B"],
            "Shortstop":      ["SS"],
            "Centerfielder":  ["CF", "OF"],
            "Outfielder":     ["OF"],
            "Leftfielder":    ["OF"],
            "Rightfielder":   ["OF"]}
    brPositions = [position.strip() for position in primaryPosition.split(",|and")]
    for position in brPositions:
        if position in positionDict.keys():
            for pos in positionDict[position]:
                if pos not in positions:
                    positions.append(pos)
                    if args.verbose: print("Adding position {position}".format(position=pos))
        elif "U" not in positions:
            positions.append("U")
            if args.verbose: print("Adding position U")

    return positions


def parseBattingTable(battingTable, args):
    if not battingTable: return {}
    battingStats = {}
    battingTable = battingTable.tbody.select("tr.full")

    if args.verbose: print("Processing {season} seasons of major league batting stats".format(season=len(battingTable)))

    for season in battingTable:
        seasonStats = {}
        stats       = season.find_all("td")

        seasonStats["year"]  = iint(stats[0].find(string=True))
        seasonStats["age"]   = iint(stats[1].find(string=True))
        seasonStats["level"] = "mlb"
        seasonStats["2b"]    = iint(stats[9].find(string=True))
        seasonStats["3b"]    = iint(stats[10].find(string=True))
        seasonStats["bb"]    = iint(stats[15].find(string=True))
        seasonStats["cs"]    = iint(stats[14].find(string=True))
        seasonStats["g"]     = iint(stats[4].find(string=True))
        seasonStats["gdp"]   = iint(stats[23].find(string=True))
        seasonStats["h"]     = iint(stats[8].find(string=True))
        seasonStats["hbp"]   = iint(stats[24].find(string=True))
        seasonStats["hr"]    = iint(stats[11].find(string=True))
        seasonStats["ibb"]   = iint(stats[27].find(string=True))
        seasonStats["pa"]    = iint(stats[5].find(string=True))
        seasonStats["r"]     = iint(stats[7].find(string=True))
        seasonStats["rbi"]   = iint(stats[12].find(string=True))
        seasonStats["sb"]    = iint(stats[13].find(string=True))
        seasonStats["sf"]    = iint(stats[26].find(string=True))
        seasonStats["sh"]    = iint(stats[25].find(string=True))
        seasonStats["so"]    = iint(stats[16].find(string=True))

        year  = seasonStats["year"]
        level = seasonStats["level"]

        battingStats[year]        = {}
        battingStats[year][level] = seasonStats

        if args.verbose: print("Processed {season} from {level} level".format(season=year, level=level))
        if args.verbose: print("{stats}".format(stats=seasonStats))

    return battingStats


def parsePitchingTables(pitchingTable, advancedPathTag, args):
    if not pitchingTable: return {}
    pitchingStats = {}
    pitchingTable = pitchingTable.tbody.select("tr.full")

    if args.verbose: print("Processing {seasons} seasons of major league pitching stats".format(seasons=len(pitchingTable)))

    advancedStats = parseAdvancedPitchingTable(advancedPathTag, args)

    for season in pitchingTable:
        seasonStats = {}
        stats       = season.find_all("td")

        seasonStats["year"]  = iint(stats[0].find(string=True))
        seasonStats["age"]   = iint(stats[1].find(string=True))
        seasonStats["level"] = "mlb"
        seasonStats["bb"]    = iint(stats[19].find(string=True))
        seasonStats["bk"]    = iint(stats[23].find(string=True))
        seasonStats["cg"]    = iint(stats[11].find(string=True))
        seasonStats["er"]    = iint(stats[17].find(string=True))
        seasonStats["g"]     = iint(stats[8].find(string=True))
        seasonStats["gs"]    = iint(stats[9].find(string=True))
        seasonStats["h"]     = iint(stats[15].find(string=True))
        seasonStats["hbp"]   = iint(stats[22].find(string=True))
        seasonStats["hr"]    = iint(stats[18].find(string=True))
        seasonStats["ibb"]   = iint(stats[20].find(string=True))
        seasonStats["ip"]    = ffloat(stats[14].find(string=True))
        seasonStats["l"]     = iint(stats[5].find(string=True))
        seasonStats["sho"]   = iint(stats[12].find(string=True))
        seasonStats["so"]    = iint(stats[21].find(string=True))
        seasonStats["sv"]    = iint(stats[13].find(string=True))
        seasonStats["w"]     = iint(stats[4].find(string=True))
        seasonStats["wp"]    = iint(stats[24].find(string=True))

        year  = seasonStats["year"]
        level = seasonStats["level"]
        if year in advancedStats.keys() and level in advancedStats[year].keys():
            seasonStats["bs"]  = advancedStats[year][level]["bs"]
            seasonStats["hld"] = advancedStats[year][level]["hld"]
            seasonStats["qs"]  = advancedStats[year][level]["qs"]
        else:
            seasonStats["bs"]  = 0
            seasonStats["hld"] = 0
            seasonStats["qs"]  = 0

        pitchingStats[year]        = {}
        pitchingStats[year][level] = seasonStats

        if args.verbose: print("Processed {season} from {level} level".format(season=year, level=level))
        if args.verbose: print("{stats}".format(stats=seasonStats))

    return pitchingStats


def parseAdvancedPitchingTable(advancedPathTag, args):
    if not advancedPathTag: return {}
    advancedPath  = advancedPathTag.get("href")
    soup = BeautifulSoup(requests.get("{domain}/{pathStr}".format(domain=args.domain[0], pathStr=advancedPath)).text, "html.parser")
    relieverTable = soup.find("table", id="pitching_reliever")
    starterTable  = soup.find("table", id="pitching_starter")

    advancedStats = {}
    relieverTable = relieverTable.tbody.select("tr.full") if relieverTable else []
    starterTable  = starterTable.tbody.select("tr.full") if starterTable else []

    for season in relieverTable:
        seasonStats = {}
        stats       = season.find_all("td")

        seasonStats["year"]  = iint(stats[0].find(string=True))
        seasonStats["level"] = "mlb"
        seasonStats["bs"]    = iint(stats[11].find(string=True))
        seasonStats["hld"]   = iint(stats[14].find(string=True))

        year  = seasonStats["year"]
        level = seasonStats["level"]

        advancedStats[year]        = {}
        advancedStats[year][level] = seasonStats

    for season in starterTable:
        year  = iint(stats[0].find(string=True))
        level = "mlb"
        qs    = iint(stats[18].find(string=True))

        advancedStats[year]              = {}
        advancedStats[year][level]["qs"] = qs

    for year in advancedStats.keys():
        for level in year.keys():
            seasonKeys = level.keys()
            if "bs" not in seasonKeys: advancedStats[year][level]["bs"] = 0
            if "hld" not in seasonKeys: advancedStats[year][level]["hld"] = 0
            if "qs" not in seasonKeys: advancedStats[year][level]["qs"] = 0

    return advancedStats


def parsePlayerIndex(args):
    paths = []
    soup  = BeautifulSoup(requests.get("{domain}/players/".format(domain=args.domain[0])).text, "html.parser")

    lettersTags = soup.select("tr td.xx_large_text.bold_text a[href]")
    [paths.append(tag["href"]) for tag in lettersTags]
    if args.verbose: print("Found {numPaths} last names indices to search".format(numPaths=len(paths)))

    return paths


def parseLetterIndex(path, args):
    paths = []
    soup  = BeautifulSoup(requests.get("{domain}/{pathStr}".format(domain=args.domain[0], pathStr=path)).text, "html.parser")

    playerTags = soup.select("blockquote pre a[href]")
    # when updating, run check aginst DB here on which players to process
    [paths.append(tag["href"]) for tag in playerTags]
    if args.verbose: print("Found {numPaths} players to process".format(numPaths=len(paths)))

    return paths


def parseArgs(args):
    parser = argparse.ArgumentParser(description = "Scrapes baseball-reference.com for player statistics")

    parser.add_argument("-d", "--domain", help="domain to scrape for statistics. Default is baseball-reference.com", nargs=1, default=["http://www.baseball-reference.com"])
    parser.add_argument("-f", "--filename", help="database file to store data in", required=True, nargs=1, type=argparse.FileType("r+"))
    parser.add_argument("-r", "--reset", help="removes database before scraping all data from baseball-reference. Conflicts with -u. One of -r and -u must be specified", action="store_true")
    parser.add_argument("-u", "--update", help="scrapes baseball-reference and adds all new information to the database. Conflicts with -r. One of -r and -u must be specified", action="store_true")
    parser.add_argument("--verbose", help="enables verbose output", action="store_true")
    parser.add_argument("--version", help="prints out version and exits", action="version", version="%(prog)s ({version})".format(version=__version__))

    parsedArgs = parser.parse_args()

    if parsedArgs.reset == parsedArgs.update:
        parser.error("-r and -u are conflicting flags. Exactly one must be specified")
        parser.print_help()

    return parsedArgs


def main(args):
    playerIDs = []
    letters = parsePlayerIndex(args)
    for letter in letters:
        profiles = parseLetterIndex(letter, args)
        for profile in profiles:
            ids = parsePlayerProfile(profile, args)
            if ids not in playerIDs:
                playerIDs.append(ids)
            else:
                print("overlapping IDs")


if __name__ == "__main__":
    parsedArgs = parseArgs(sys.argv)
    main(parsedArgs)

