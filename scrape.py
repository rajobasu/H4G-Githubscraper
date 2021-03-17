import pickle

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import config
import logging


class Profile:
    def __init__(self, driver, profile):
        self.have_recent_activities = False
        self.LinkedIn_Dict = {}
        self.driver = driver
        self.profile = profile

        self.login(email=config.email, password=config.password)
        self.driver.get(self.profile)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pv-top-card--list.inline-flex.align-items-center")))
        logging.info("successfully fetched profile")

    def scrape(self):
        self.printProgressBar(0, 7, "checking for recent activities\t", "Complete", length=50, printEnd="\r\n")
        self.check_recent_activities()
        self.printProgressBar(1, 7, "fetching profile picture\t\t", "Complete", length=50, printEnd="\r\n")
        self.fetch_profile_picture()
        self.printProgressBar(2, 7, "fetching interest categories\t", "Complete", length=50, printEnd="\r\n")
        self.fetch_interest_categories()
        self.printProgressBar(5, 7, "fetching recent activities\t\t", "Complete", length=50, printEnd="\r\n")
        self.fetch_recent_activies()
        self.printProgressBar(6, 7, "cleaning up\t\t\t\t\t\t", "Complete", length=50, printEnd="\r\n")
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        self.driver.quit()
        self.printProgressBar(7, 7, "exiting\t\t\t\t\t\t\t", "Complete", length=50, printEnd="\r\n")

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

    def fetch_profile_picture(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "presence-entity.presence-entity--size-9.pv-top-card__image")))
        profile_pic = self.driver.find_element_by_class_name(
            "presence-entity.presence-entity--size-9.pv-top-card__image").find_element_by_xpath("./img")
        if "data:image/gif" in profile_pic.get_attribute('src'):
            self.LinkedIn_Dict["Profile Picture"] = None
            logging.warning("no profile picture")
        else:
            self.LinkedIn_Dict["Profile Picture"] = profile_pic.get_attribute('src')
            logging.info("successfully fetched profile picture")

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
                    description = self.driver.find_element_by_class_name(
                        "pv-about__summary-text.mt4.t-14.ember-view").text
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
                company_sector = self.driver.find_element_by_class_name(
                    "org-top-card-summary-info-list__info-item").text
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

    def login(self, email=None, password=None):
        self.driver.get("https://www.linkedin.com/login")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "username")))

        email_elem = self.driver.find_element_by_id("username")
        email_elem.send_keys(email)

        password_elem = self.driver.find_element_by_id("password")
        password_elem.send_keys(password)
        password_elem.submit()

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "profile-nav-item")))
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "profile-rail-card__actor-link.t-16.t-black.t-bold")))

    def printProgressBar(self, iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
        # Print New Line on Complete
        if iteration == total:
            print()


def linkedin_scrapper(profile_link):
    logging.basicConfig(filename='scrape.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

    options = Options()
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    try:
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
    except:
        pass

    logging.info("driver setup done")

    scraper = Profile(driver=driver, profile=profile_link)

    scraper.scrape()
    return scraper.LinkedIn_Dict


if __name__ == "__main__":
    linkedin_scrapper("xxx")
