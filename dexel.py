from bs4 import BeautifulSoup
import requests
import json
import sqlite3 as sq
import pandas as pd
import time

def dexel_values():

    widths = []
    profiles = []
    rims = []
    
    keys={"width":widths,
          "profile":profiles,
          "rim":rims}
    
    URL = "http://www.dexel.co.uk"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    
    for name in ["width","profile","rim"]:
        items = soup.find(id=f"tyre{name}select")
        items = items.find_all("option")
        for item in items:
            item = item.text
            try:
                float(item)
            except:
                    continue
            else:
                keys[name].append(item)
    return(widths,profiles,rims)

def report(filename):
    conn = sq.connect(filename)
    data=pd.read_sql("SELECT * FROM UniqueTyres", conn, index_col="id")
    conn.close()
    data.to_csv("tyreStatsUnique.csv", header=False)
    return data

def scrape_dexel(width, profile, rim):
    conn = sq.connect("Database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS UniqueTyres (id INTEGER PRIMARY KEY AUTOINCREMENT, Brand TEXT, Pattern CHAR(20), Size CHAR(20),Price REAL, Seasonality TEXT, Website CHAR(50), UNIQUE(Brand, Pattern, Size, Price, Seasonality, Website))")
    URL = f"http://www.dexel.co.uk/shopping/tyre-results?width={width}&profile={profile}&rim={rim}&speed=."
    page = requests.get(URL)
    
    soup = BeautifulSoup(page.content, "html.parser")
    script = soup.find_all("script")[7].string.splitlines()[1]
    tyres = script.split("allTyres = ", 1)[-1].rsplit(';', 1)[0]
    tyres = json.loads(tyres)
    print(f"Found {len(tyres)} tyres")
    for i in range(len(tyres)-1):
        tyre = tyres[i]
        
        website = "www.dexel.co.uk"
        price = tyre["price"]
        brand = tyre["manufacturer"]
        size = f"{width}/{profile} R{rim}"
        pattern = tyre["pattern_name"]
        
        if tyre["winter"] == "1":
            seasonality = "winter"
        else:
            seasonality = "summer"

            conn.execute("INSERT OR IGNORE INTO UniqueTyres (Brand, Pattern, Size, Price, Seasonality, Website) VALUES (?, ?, ?, ?, ?, ?)", (brand,pattern,size,price,seasonality,website))
            print(f"Inserted {pattern} from {website}")
    conn.commit()
    print("Committed")
    
    return

    URL = "http://www.dexel.co.uk"
    page = requests.get(URL)

def scrape_dexel_loop():
    i=1
    widths,profiles,rims=dexel_values()
    total = len(widths)*len(profiles)*len(rims)
    for width in widths:
        for profile in profiles:
            for rim in rims:
                time.sleep(2)
                print(f"\nscraping page {i}/{total} ({width}/{profile} R{rim}) ({100*i/total:.2f}%)")
                scrape_dexel(width, profile, rim)
                print("Finished")
                i+=1
    data = report("Database.db")
    return data
