import re
import primp
from bs4 import BeautifulSoup


def scraper(url: str) -> str:
    client = primp.Client(impersonate="chrome_124", verify=False)
    resp = client.get(url)

    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "lxml").get_text()

        return soup.replace("\n", "").replace("\t", "").replace("\r", "")
    else:
        return f"Cannot get the content of {url}!"


def reader(url) -> str:
    client = primp.Client(impersonate="chrome_124", verify=False)
    resp = client.get(url="https://r.jina.ai/" + url)
    if resp.status_code == 200:
        return resp.text
    else:
        return f"Cannot get the content of {url}!"


# TODO: Too slow, will be removed soon.
def clean(raw_text) -> str:
    unescaped_text = raw_text.encode("utf-8").decode("unicode_escape")

    html_entities = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        "&#39;": "'",
        "&ldquo;": '"',
        "&rdquo;": '"',
        "&lsquo;": """, '&rsquo;': """,
    }
    for entity, char in html_entities.items():
        unescaped_text = unescaped_text.replace(entity, char)

    standardized_text = unescaped_text.replace("\r\n", "\n").replace("\r", "\n")

    no_tabs_text = standardized_text.replace("\t", " ")

    cleaned_text = "".join(
        char for char in no_tabs_text if char == "\n" or ord(char) >= 32
    )

    single_spaced_text = re.sub(r" +", " ", cleaned_text)
    single_newline_text = re.sub(r"\n+", "\n", single_spaced_text)

    final_text = "\n".join(
        line.strip() for line in single_newline_text.splitlines()
    ).strip()

    non_empty_lines = [line for line in final_text.splitlines() if line.strip()]
    clean_text = "\n".join(non_empty_lines)

    return clean_text
