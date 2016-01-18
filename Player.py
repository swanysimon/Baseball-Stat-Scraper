#!/usr/bin/env python3


"""Player.py: provides the framework for storing information on baseball players"""

__author__      = "Simon Swanson"
__copyright__   = "Copyright 2015, Simon Swanson"
__license__     = "GPL"
__version__     = "1.0.0"
__maintainer__  = "Simon Swanson"


class Player(object):

    def __init__(self, playerID, fullName, rosterName, birthday, retired):
        self.playerID  = playerID
        self.name      = rosterName
        self.fullName  = fullName
        self.birthday  = birthday
        self.retired   = retired
        self.seasons   = {}

    def getAge(self):
        return self.birthday

    def getName(self):
        return self.name

    def getplayerID(self):
        return self.playerID

    def getStats(self):
        return self.seasons

    def isRetired(self):
        return self.retired

    def addStats(self, seasonDict, category):
        for season in seasonDict.keys():
            self.addStat(season, seasonDict[season], category)

    def addStat(self, season, seasonStats, category):
        if category not in self.seasons.keys():
            self.seasons[category] = {}
        if season not in self.seasons[category].keys():
            self.seasons[category][season] = {}
        for stat in seasonStats.keys():
            if stat in self.seasons[category][season].keys():
                if self.seasons[category][season][stat] == seasonStats[stat]:
                    print("Replacing {season}'s {stat} value {oldValue} with {newValue}".format(season=season, 
                            stat=stat, 
                            oldValue=self.seasons[category][season][stat],
                            newValue=seasonStats[stat]))
            self.seasons[category][season][stat] = seasonStats[stat]

    def addPositions(self, positionDict):
        self.addStats(positionDict, "fielding")

    def addPosition(self, season, position, gamesPlayed):
        positionDict = {}
        positionDict[position] = gamesPlayed
        self.addStat(season, positionDict, "fielding")

    def __str__(self):
        return "Player(playerID='{playerID}', rosterName='{rosterName}', fullName='{fullName}', birthday='{birthday}', retired={retired}, positions={positions}, seasons={seasons})".format(
                playerID=self.playerID,
                rosterName=self.name,
                fullName=self.fullName,
                birthday=self.birthday,
                retired=self.retired,
                positions=self.positions,
                seasons=self.seasons)


def version():
    print("Player ({version})".format(version=__version__))

