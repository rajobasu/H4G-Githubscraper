import config
import json
import requests


def read_from_json(file_name: str) -> dict:
    with open(file_name, 'r') as json_file:
        return json.load(json_file)


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


def main():
    file_name = 'RY.json'
    person_dict = read_from_json(file_name=file_name)
    person = KeywordExtractor(person_dict=person_dict)
    print(person.keywords)


if __name__ == "__main__":
    main()
