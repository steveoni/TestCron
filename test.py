import time

from bs4 import BeautifulSoup
from dataflows import (
    add_metadata,
    dump_to_path,
    load,
    validate,
    printer,
    Flow,
    PackageWrapper,
    ResourceWrapper,
)
from html_table_extractor.extractor import Extractor

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

options = webdriver.FirefoxOptions()
options.headless = True
driver = webdriver.Firefox(options=options)
def get_data():
    driver.get("https://www.iso.org/obp/ui/#search")
    delay = 40
    try:
        # Check proper radio button
        radio = WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.ID, "gwt-uid-12"))
        )
        radio.click()
        # Click search
        search = driver.find_element_by_xpath(
            "//*[@id='obpui-105541713']/div/div[2]/div/"
            "div/div[2]/div/div/div[2]/div/div/div/div/"
            "div/div[2]/div/div[2]/div/div[2]/div/div/div[4]/div/span"
        )
        search.click()
        # Load 300 countries instead of 25
        select = WebDriverWait(driver, delay).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[1]/div/div[2]/div/div/div[2]/div/"
                    "div/div[2]/div/div/div/div/div/div[1]/div/div[5]"
                    "/div[3]/div/select/option[8]",
                )
            )
        )
        select.click()
        # Wait until last item is loaded
        _ = WebDriverWait(driver, 100).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='obpui-105541713']/div/div[2]/div/div/div[2]/"
                    "div/div/div[2]/div/div/div/div/div/div[2]/div/div[2]/"
                    "div/div/div[2]/div/div[2]/div[2]/div[3]/table/tbody/tr[249]",
                )
            )
        )

        time.sleep(200)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        tables = soup.find("table", attrs={"role": "grid"})
        headers = [ t.text for t in tables.find("thead").find('tr').find_all('th')]
        countries = tables.find("tbody").find_all('tr')
        countries = [ [t.text for t in county.find_all('td')] for county in countries]

        for country in countries:
            info = {}
            for idx, header in enumerate(headers):
                info[header] = country[idx].replace("*","")
            yield info

    except TimeoutException:
        print("Loading took too much time!")


def add_columns_to_schema(package):
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="Full name", type="string")
    )
    package.pkg.descriptor["resources"][0]["schema"]["fields"].append(
        dict(name="Independent", type="string")
    )

    yield package.pkg
    yield from package


def add_info(row):
    driver.get(
        "https://www.iso.org/obp/ui/#iso:code:3166:{}".format(
            row["Alpha-2 code"]
        )
    )
    delay = 1.5
    time.sleep(delay)
    WebDriverWait(driver, delay).until(
        EC.presence_of_element_located((By.CLASS_NAME, "core-view-summary"))
    )
    headers = driver.find_elements(by=By.CLASS_NAME, value="core-view-field-name")
    values = driver.find_elements(by=By.CLASS_NAME, value="core-view-field-value")
    needed = ["Full name", "Independent"]
    for header, value in zip(headers, values):
        header = header.text.strip()
        if header in needed:
            row[header] = value.text.strip()


def rename(package: PackageWrapper):
    package.pkg.descriptor["resources"][0]["name"] = "iso-countries"
    package.pkg.descriptor["resources"][0]["path"] = "iso-countries.csv"
    yield package.pkg
    res_iter = iter(package)
    first: ResourceWrapper = next(res_iter)
    yield first.it
    yield from package


country_info_iso = Flow(
    load("country_info_iso_res_1.csv"),
    add_metadata(name="iso-country-codes"),
    add_columns_to_schema,
    rename,
    add_info,
    validate(),
    printer(num_rows=5),
    dump_to_path("data/country_info_iso"),
)


if __name__ == "__main__":
    options = webdriver.FirefoxOptions()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    country_info_iso.process()
    driver.quit()