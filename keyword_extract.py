import config
import requests
from scrape import linkedin_scrapper


class KeywordExtractor:
    def __init__(self, person_dict):
        self.text = ""
        self.person_dict = person_dict
        self.keywords = ""

        self.extract_information()
        if self.text != "":
            self.extract_keywords()

    def extract_information(self):
        for x in self.person_dict["Interests"].keys():
            if x == 'Companies':
                pass
            elif x == 'Influencers':
                y = self.person_dict["Interests"][x]
                for z in y:
                    self.text += z["Description"] + '. '

        if "Recent Activities" in self.person_dict:
            for x in self.person_dict["Recent Activities"]:
                    y = x["Author Description"]
                    self.text += (y+'. ') if y is not None else ''

    def extract_keywords(self):
        r = requests.post(
            "https://api.deepai.org/api/text-tagging",
            data={'text': self.text},
            headers={'api-key': config.api_key}
        )
        self.keywords = r.json()['output']


def linkedin_data(profile_link):

    person_dict = linkedin_scrapper(profile_link=profile_link)
    person = KeywordExtractor(person_dict=person_dict)
    person_dict["keywords"] = person.keywords.split("\n")
    return person_dict


if __name__ == "__main__":
    print(linkedin_data("https://www.linkedin.com/in/richardyang98/"))
