# import requests
import pyreqwest_impersonate as pri

from bs4 import BeautifulSoup


def scrape(url: str) -> str:
    client = pri.Client(impersonate="chrome_124", verify=False)

    site = client.get(url)
    if site.status_code == 200:
        soup = BeautifulSoup(site.text, "lxml").get_text()
        if "\n" in soup:
            if "\t" in soup:
                soup = soup.replace("\n", "")
                soup = soup.replace("\t", " ")
            return soup
        else:
            return soup
    else:
        return "Cannot scrape site"
