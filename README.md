thebaseballcubeScraper.py
========================

Extracts stats from thebaseballcube.com for each active player's stats. The choice to switch to thebaseballcube from baseball-reference was their inclusion of holds and quality starts, a statistic in many fantasy leagues.

Future functionality should include the ability to search for college and minor league statistics, but those are currently in the works and may take a while to work with, since the priority is to retrieve stats for major league players. The data is stored in an XML file for future use, though I'm not sure if XML is the format I should be using for this.

Makes use of the BeautifulSoup module to both extract information from the HTML files and to generate the XML. Again, I'm sure there's a more efficient way to do this, but that's what I'm working with for now.


baseball-reference.Extraction.py
========================

Extracts stats from baseball-reference.com of each active player's major league stats.

The baseball-reference.Extraction.py only takes in player stats and does not evaluate. However, stores in a file in a single dictionary for easy future access.

Calculator.redditdynasty2.py is an example of how this data might be applied. This particular calculator was built around a specific points system for a fantasy baseball league.
