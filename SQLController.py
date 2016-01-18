#!/usr/bin/env python3


"""SQLController.py: provides the framework for storing and retrieving player data from a sqlite database"""

__author__      = "Simon Swanson"
__copyright__   = "Copyright 2015, Simon Swanson"
__license__     = "GPL"
__version__     = "1.0.0"
__maintainer__  = "Simon Swanson"


from Player import Player
import sqlite3


class SQLController(object):

    def __init__(self, dbName):
        self.conn = sqlite3.connect(dbName)
        self.cur  = self.conn.cursor()

    def resetDB(self):
        self.run("drop table if exists br_reddit_dynasty_info")
        self.run("drop table if exists br_hitting_stats")
        self.run("drop table if exists br_pitching_stats")
        self.run("drop table if exists br_position_info")
        self.run("drop table if exists br_season_info")
        self.run("drop table if exists br_player_index")
        self.run("drop table if exists br_player_info")

    def query(self, arg):
        self.cur.execute(arg)
        self.conn.commit()
        return self.cur

    def run(self, arg):
        self.cur.execute(arg)
        self.conn.commit()

    def __del__(self):
        self.conn.close()


def reddityDynastyOwners():
    owners = []
    return owners


def version():
    print("Player ({version})".format(version=__version__))
