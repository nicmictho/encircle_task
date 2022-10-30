from bs4 import BeautifulSoup
import requests
import sqlite3 as sq
import pandas as pd
import time

def national_values():
    widths = []
    profiles = []
    rims = []
    
    keys={
        "Width":widths,
        "Profile":profiles,
        "Diameter":rims
        }
    
    URL = "http://www.national.co.uk"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    
    
    for name in ["Width","Profile","Diameter"]:
        data = soup.find("div", class_="col-xs-12 text-center form-inline")
        data = data.find(id=f"PageContent_ucTyreSearch_ddl{name}")
        items = data.find_all("option")
        for item in items:
            item = item.text
            try:
                float(item)
            except:
                    continue
            else:
                keys[name].append(item)
                
    return widths,profiles,rims

def report(filename):
    conn = sq.connect(filename)
    data=pd.read_sql("SELECT * FROM UniqueTyres", conn, index_col="id")
    conn.close()
    data.to_csv("tyreStatsUnique.csv", header=False)
    return data

def scrape_national(width, profile, rim):
    conn = sq.connect("Database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS UniqueTyres (id INTEGER PRIMARY KEY AUTOINCREMENT, Brand TEXT, Pattern CHAR(20), Size CHAR(20),Price REAL, Seasonality TEXT, Website CHAR(50), UNIQUE(Brand, Pattern, Size, Price, Seasonality, Website))")
    
    URL = f"https://www.national.co.uk/tyres-search?width={width}&profile={profile}&diameter={rim}"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    
    i=0
    while True:
        tyre = soup.find(id=f"PageContent_ucTyreResults_rptTyres_divTyre_{i}")
        if (tyre) == None:
            conn.commit()
            print("Committed")
            return
        
        website = "www.national.co.uk"
        price = tyre["data-sort"]
        brand = tyre["data-brand"]
        seasonality = tyre["data-tyre-season"]
        size = f"{width}/{profile} R{rim}"
        pattern = tyre.find(id=f"PageContent_ucTyreResults_rptTyres_hypPattern_{i}").text
  

        conn.execute("INSERT OR IGNORE INTO UniqueTyres (Brand, Pattern, Size, Price, Seasonality, Website) VALUES (?, ?, ?, ?, ?, ?)",(brand,pattern,size,price,seasonality,website))
        print(f"Inserted {pattern} from {website}")
        i+=1

def scrape_national_loop():
    i=1
    widths,profiles,rims=national_values()
    total = len(widths)*len(profiles)*len(rims)
    for width in widths:
        for profile in profiles:
            for rim in rims:
                time.sleep(2)
                print(f"\nscraping page {i}/{total} ({width}/{profile} R{rim}) ({100*i/total:.2f}%)")
                scrape_national(width, profile, rim)
                print("Finished")
                i+=1
    data = report("Database.db")
    return data