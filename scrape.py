from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from helper import login, printProgressBar
import config
import json
import logging


class Profile:
    def __init__(self, driver, profile):
        self.have_recent_activities = False
        self.LinkedIn_Dict = {}
        self.driver = driver
        self.profile = profile

        self.driver.get(self.profile)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card--list.inline-flex.align-items-center")))
        logging.info("successfully fetched profile")

    def scrape(self):
        printProgressBar(0, 6, "checking for recent activities\t", "Complete", length=50, printEnd="\r\n")
        self.check_recent_activities()
        printProgressBar(1, 6, "fetching interest categories\t", "Complete", length=50, printEnd="\r\n")
        self.fetch_interest_categories()
        printProgressBar(4, 6, "fetching recent activities\t\t", "Complete", length=50, printEnd="\r\n")
        self.fetch_recent_activies()
        printProgressBar(5, 6, "cleaning up\t\t\t\t\t\t", "Complete", length=50, printEnd="\r\n")
        self.driver.quit()
        printProgressBar(6, 6, "exiting\t\t\t\t\t\t\t", "Complete", length=50, printEnd="\r\n")

        logging.info("finished scrapping")

    def check_recent_activities(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "pv-recent-activity-section-v2__summary.t-14.t-black--light.t-normal")))
        if "last 90 days are displayed here" not in \
                self.driver.find_element_by_class_name(
                    "pv-recent-activity-section-v2__summary.t-14.t-black--light.t-normal").text:
            self.have_recent_activities = True
        else:
            logging.warning("no recent activities")

    def fetch_interest_categories(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        self.LinkedIn_Dict['Interests'] = {}
        self.driver.get(self.profile + '/detail/interests/')
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'pv-interests-modal__following')]")))
        interest_categories = self.driver.find_elements_by_xpath("//*[contains(@id, 'pv-interests-modal__following')]")

        for interest_category in interest_categories:
            self.LinkedIn_Dict['Interests'][interest_category.text] = interest_category.get_attribute('href')

        logging.info("successfully fetched interest categories")
        logging.debug('found', len(self.LinkedIn_Dict['Interests']), 'interest categories')

        i = 1
        for key, values in self.LinkedIn_Dict['Interests'].items():
            self.driver.get(values)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pv-entity__summary-title-text")))
            WebDriverWait(self.driver, 1)
            if key == 'Influencers':
                interest_names = self.driver.find_elements_by_class_name("pv-entity__summary-title-text")
                interest_descriptions = self.driver.find_elements_by_class_name("pv-interest-entity-link.ember-view")
                self.LinkedIn_Dict['Interests'][key] = [
                    {'Name': interest_name.text, 'Description': interest_description.get_attribute("href")}
                    for interest_name, interest_description in zip(interest_names, interest_descriptions)]
            elif key == 'Companies':
                interest_names = self.driver.find_elements_by_class_name("pv-entity__summary-title-text")
                company_links = self.driver.find_elements_by_class_name("pv-interest-entity-link.ember-view")
                self.LinkedIn_Dict['Interests'][key] = [
                    {'Name': interest_name.text, 'Industry': link.get_attribute("href")}
                    for interest_name, link in zip(interest_names, company_links)]
            # else:
            #     interest_names = driver.find_elements_by_class_name("pv-entity__summary-title-text")
            #     LinkedIn_Dict['Interests'][key] = [{'Name': interest_names.text} for interest_names in interest_names]
            logging.debug('fetched', i, 'interest categories')
            i += 1

        self.fetch_influencer_info()
        self.fetch_company_info()

    def fetch_influencer_info(self):
        if 'Influencers' in self.LinkedIn_Dict['Interests']:
            for index in range(len(self.LinkedIn_Dict['Interests']['Influencers'])):
                description = self.LinkedIn_Dict['Interests']['Influencers'][index]['Description']
                self.driver.get(description)
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "pv-about__summary-text.mt4.t-14.ember-view")))
                    description = self.driver.find_element_by_class_name("pv-about__summary-text.mt4.t-14.ember-view").text
                except:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "mt1.t-18.t-black.t-normal.break-words")))
                    description = self.driver.find_element_by_class_name("mt1.t-18.t-black.t-normal.break-words").text

                self.LinkedIn_Dict['Interests']["Influencers"][index]['Description'] = description
            logging.info("successfully fetched interest influencer infos")

    def fetch_company_info(self):
        if 'Companies' in self.LinkedIn_Dict['Interests']:
            for index in range(len(self.LinkedIn_Dict['Interests']['Companies'])):
                company_link = self.LinkedIn_Dict['Interests']['Companies'][index]['Industry']
                self.driver.get(company_link)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "org-top-card-summary-info-list__info-item")))
                company_sector = self.driver.find_element_by_class_name("org-top-card-summary-info-list__info-item").text
                self.LinkedIn_Dict['Interests']["Companies"][index]['Industry'] = company_sector
            logging.info("successfully fetched interest company infos")

    def fetch_recent_activies(self):
        if self.have_recent_activities:
            self.driver.get(self.profile + '/detail/recent-activity/')
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "occludable-update.ember-view")))
            RAs = self.driver.find_elements_by_class_name("occludable-update.ember-view")

            self.LinkedIn_Dict['Recent Activities'] = [{'Article Author': None,
                                                        'Author Description': None,
                                                        'Activity': None} for i in range(min(5, len(RAs)))]
            for index in range(5):
                ra = RAs[index]
                try:
                    self.LinkedIn_Dict['Recent Activities'][index]['Article Author'] = \
                        ra.find_element_by_class_name(
                            "feed-shared-actor__name.t-14.t-bold.hoverable-link-text.t-black").text
                except:
                    pass

                try:
                    description = ra.find_element_by_class_name(
                        "feed-shared-actor__description.t-12.t-normal.t-black--light").text or \
                                  ra.find_element_by_class_name(
                                      "feed-shared-text-view.white-space-pre-wrap.break-words.ember-view").text
                    self.LinkedIn_Dict['Recent Activities'][index]['Author Description'] = \
                        description if 'follower' not in description else None
                except:
                    pass

                try:
                    self.LinkedIn_Dict['Recent Activities'][index]['Activity'] = ra.find_element_by_class_name(
                        "feed-shared-text-view.white-space-pre-wrap.break-words.ember-view").text
                except:
                    pass

            logging.info('successfully fetched recent activities')


def write_to_json(file_name: str, data: any) -> None:
    with open(file_name + '.json', 'w') as json_file:
        json.dump(data, json_file)

    logging.info("json file created")


def main():
    profile = "https://www.linkedin.com/in/richardyang98/"
    file_name = 'RY'
    logging.basicConfig(filename='scrape.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    logging.info("driver setup done")

    login(driver=driver, email=config.email, password=config.password)
    scraper = Profile(driver=driver, profile=profile)
    scraper.scrape()
    write_to_json(file_name=file_name, data=scraper.LinkedIn_Dict)


if __name__ == "__main__":
    main()
