from bs4 import BeautifulSoup as bs
import requests
import sqlite3
import re

def db_build():
	"""Drops and rebuilds all tables"""
	r_conn = sqlite3.connect('barrett-jackson-scrape.db')
	r = r_conn.cursor()
	r.execute("""DROP TABLE IF EXISTS cars""")
	r.execute("""CREATE TABLE IF NOT EXISTS cars (	Lot_Name TEXT PRIMARY KEY,
													Category,
													Auction,
													Reserve,
													Status,
													Price INT,
													Lot,
													Year,
													Make,
													Model,
													Style,
													VIN,
													Exterior_Color,
													Interior_Color,
													Cylinders,
													Engine_Size,
													Transmission,
													Description TEXT)""")
	r_conn.commit()
	r_conn.close()


def upsert(primary, key, value):
	r_conn = sqlite3.connect('barrett-jackson-scrape.db')
	r = r_conn.cursor()
	r.execute("""UPDATE cars SET {0} = ? WHERE Lot_Name = ?""".format(key), (value, primary))
	r_conn.commit()
	r_conn.close()


def main(nextlink='https://www.barrett-jackson.com/Events/Event/Details/1973-OLDSMOBILE-DELTA-88-ROYALE-CUSTOM-CONVERTIBLE-177640'):
	global nextlot
	while True:
		try:
			page = requests.get(nextlink)
			break
		except:
			print("Connection Error: Retrying")
	soup = bs(page.content, 'html5lib')
	lot_name = soup.find(class_="hellcat-section-heading clearfix").div.div.strong.text.strip()

	tables = soup.find_all(class_="table table-condensed table-striped")

	r_conn = sqlite3.connect('barrett-jackson-scrape.db')
	r = r_conn.cursor()
	r.execute("""INSERT INTO cars (Lot_Name) VALUES ("{0}\")""".format(lot_name))
	r_conn.commit()
	r_conn.close()
	for tr in tables[0].tbody.find_all('tr'):
		upsert(lot_name, tr.find_all('td')[0].text.replace(" ", "_"), tr.find_all('td')[1].text)

	for tr in tables[1].tbody.find_all('tr'):
		upsert(lot_name, tr.find_all('td')[0].text.replace(" ", "_"), tr.find_all('td')[1].text)
	upsert(lot_name, "Price", re.search(r"var price = '(.*)';", soup.text).group(1).replace("$", "").replace(",", ""))
	upsert(lot_name, "Description", soup.find_all(class_="hellcat-section-inner")[1].text.strip())

	r_conn = sqlite3.connect('barrett-jackson-scrape.db')
	r = r_conn.cursor()
	print(lot_name)

	for a in soup.find_all("a", class_="btn"):
		if a.find(text=re.compile("Next Lot ")):
			nextlot = "https://www.barrett-jackson.com{0}".format(a['href'])
			with open("nextlot.txt", 'w') as file:
				file.write(nextlot)
			break


db_build()
""" Due to missing lot pages on BJ's page I've manually added these as start points for the scraper """
nextlot = [	'https://www.barrett-jackson.com/Events/Event/Details/1973-OLDSMOBILE-DELTA-88-ROYALE-CUSTOM-CONVERTIBLE-177640',
			'https://www.barrett-jackson.com/Events/Event/Details/2003-MERCEDES-BENZ-CL55-AMG-2-DOOR-COUPE-176972']

for x in nextlot:
	nextlot = x
	try:
		while True:
			main(nextlot)
	except:
		pass
