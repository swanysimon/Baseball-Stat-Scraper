thebaseballcubeScraper.py
========================

Extracts stats from thebaseballcube.com for each active player's stats. The choice to switch to thebaseballcube from baseball-reference was their inclusion of holds and quality starts on player pages, a statistic in many fantasy leagues. Baseball-reference has these statistics, just not anywhere that can be easily accessed.

My storage option of choice is SQLite because of its efficiency and native support in Python3 (or nearly native, I can't remember at this point). I previously used XML because it is easy to understand and can be read by a human, but the process of searching for players and calculating value took far too long and I'm hoping SQLite will give me a better interface and response time in that department.

redditDynastyCalc.py provides all the tools necessary to search for relevant information during the draft. Or it will when I've finished. Currently is it still in the XML processing phase, which will be fixed when I create the appropriate SQLite tables and access functions.

Future functionality should include the ability to search for college and minor league statistics, but those are currently in the works and may take a while to work with, since the priority is to retrieve stats for major league players.

Makes use of the BeautifulSoup module to both extract information from the HTML files.


baseball-reference.Extraction.py
========================

Extracts stats from baseball-reference.com of each active player's major league stats.

The baseball-reference.Extraction-OLD.py only takes in player stats and does not evaluate. However, stores in a file in a single dictionary for easy future access.

Calculator.redditdynasty2-OLD.py is an example of how this data might be applied. This particular calculator was built around a specific points system for a fantasy baseball league.
