import json
import os

from github import Github
import threading

# ==============================================================================
# CLASSES
# ==============================================================================
from github.GithubException import UnknownObjectException


class RepoFeatures:
    def __init__(self):
        self.name = None
        self.java_lines = 0
        self.keywords = {}
        self.jarFilesUsed = []
        self.forkedRepos = 0
        self.totalRepos = 0
        self.repo_stars = {}
        self.extensions = {}
        pass

    def set_name(self, name):
        self.name = name

    def add_java_lines(self, lines):
        self.java_lines += lines

    def add_keyword(self, keyword):
        if keyword in self.keywords:
            self.keywords[keyword] += 1
        else:
            self.keywords[keyword] = 1

    def add_jar(self, jar):
        self.jarFilesUsed.append(jar)

    def add_forked_repo(self):
        self.forkedRepos += 1

    def add_repo_stars(self, repo_name, stars):
        if stars != 0:
            self.repo_stars[repo_name] = stars

    def add_repo(self):
        self.totalRepos += 1

    def add_extension(self, e):
        if e in self.extensions:
            self.extensions[e] += 1
        else:
            self.extensions[e] = 1

    def process_extension_to_percentages(self):
        total = 0
        for key, value in self.extensions.items():
            total += value
        total2 = 0
        ex = {}
        t = None
        v2 = 0
        print(total)
        print(self.extensions)
        for key, value in self.extensions.items():
            v = value * 100 // total
            total2 += v
            ex[key] = v
            if v > v2:
                v2 = v
                t = key
        print(ex)
        if t is not None:
            ex[t] += 100 - total2

        self.extensions = ex


# ==============================================================================
# FUNCTIONS
# ==============================================================================
valid_extensions = {".java": "java",
                    ".js": "javascript",
                    ".php": "PHP",
                    ".py": "python",
                    ".vbs": "VBScript",
                    ".cpp": "C++",
                    ".c": "C",
                    ".css": "HTML/CSS",
                    ".html": "HTML/CSS",
                    ".rb": "Ruby",
                    ".swift": "Swift",
                    ".kt": "Kotlin"}
dir_to_avoid = ["vendor"]



def has_valid_extension(path):
    if "." not in path:
        return True
    else:
        for ext in valid_extensions:
            if path.endswith(ext):
                return True

    return False


def get_repos_list(user):
    return user.get_repos()


def get_github_obj():
    access_token = str(os.environ["github_api_key"])
    g = Github(access_token)
    return g


def get_user(github_obj, name):
    return github_obj.get_user(name)


def get_repo_stats(repo):
    rf = RepoFeatures()
    rf.set_name(repo.name)
    return rf


def get_extension(str):
    for key, value in valid_extensions.items():
        if str.endswith(key):
            return value
    return None


# ======================================================================
# ======== FUNCTIONS FOR FILE PROCESSING ===============================
# ======================================================================


def process_java_file(file_content, repo_features):
    lines = file_content.split("\n")
    for line in lines:
        line.strip()
        if line.startswith("import"):
            line = line[len("import "):]
            if line.strip().startswith("java") or line.strip().startswith("org"):
                repo_features.add_keyword(line.strip())


def process_file(file, repo_features):
    extension = get_extension(file.name)
    if extension is None:
        return
    repo_features.add_extension(extension)
    if file.name.endswith("java"):
        process_java_file(str(file.decoded_content, 'utf-8'), repo_features)
    elif file.name.endswith("jar"):
        repo_features.add_jar(file.name)


def get_content_of_current_path(repo, current_path):
    max_try = 100
    curr_try = 0
    got = False
    while not got and curr_try < max_try:
        try:
            contents = repo.get_contents(current_path)
            got = True
        except:
            curr_try += 1

    if not got:
        return None

    return contents


def process_repo_recursively(repo, repo_features, current_path, src_found=False, dir_depth_count=0):
    if src_found is False and dir_depth_count > 3:
        return
    # this part is to ge the content of the current path
    contents = get_content_of_current_path(repo, current_path)

    for file in contents:
        if file.type == "dir":
            ok = True
            for v in dir_to_avoid:
                if v in file.name:
                    ok = False
                    break
            if not ok:
                continue
            if file.name == "src":
                process_repo_recursively(repo, repo_features, file.path, True, dir_depth_count + 1)
            else:
                process_repo_recursively(repo, repo_features, file.path, src_found, dir_depth_count + 1)
        else:
            print("Processing : ", file.name)
            process_file(file, repo_features)


def process_entire_repo(repo, repo_features):
    print("-" * 40)
    print(repo.name)
    print(repo.fork)
    process_repo_recursively(repo, repo_features, "")
    print("-" * 40)


def get_all_files_from_commit(commit):
    allfiles = []
    for file in commit.files:
        path = file.filename
        print("PATH : ", path)
        allfiles.append(path)
    return allfiles


def process_repo_commit_wise(repo, repo_features, username):
    print(username)
    all_commits = repo.get_commits(author=username)
    print(all_commits.totalCount)
    all_files = []
    for commit in all_commits:
        all_files = all_files + get_all_files_from_commit(commit)

    all_files = list(dict.fromkeys(all_files))
    for file in all_files:
        try:
            actual_file = repo.get_contents(file)
            process_file(actual_file, repo_features)
        except:
            """Essentially to deal with deletion"""
            pass


# ======================================================================
# ======== FUNCTIONS FOR CONCEPT EXTRACTION ============================
# ======================================================================

def get_associated_concept_from_keyword(keyword):
    parts = keyword.split(".")
    if len(parts) == 1:
        return parts[0]

    main_part = parts[0] + "." + parts[1]
    return main_part


def process_all_keywords(keywords):
    concept_frequency_dict = {}
    for keyword, freq in keywords.items():
        concept = get_associated_concept_from_keyword(keyword)
        if concept in concept_frequency_dict:
            concept_frequency_dict[concept] += freq
        else:
            concept_frequency_dict[concept] = freq
    return concept_frequency_dict


def get_top_keywords(cf_dict, num):
    num = min(num, len(cf_dict))
    all_pairs = []
    sorted_keys = sorted(cf_dict.keys(), key=cf_dict.get, reverse=True)
    for i in range(num):
        all_pairs.append((sorted_keys[i], cf_dict[sorted_keys[i]]))

    return all_pairs


def load_mappings():
    mappings = {}
    with open("framework-features.csv", "r") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split(",")
            mappings[parts[0]] = parts[1]

    return mappings


def find_concept(mappings, keyword):
    for phrase, concept in mappings.items():
        if phrase in keyword:
            return concept
    return None


def process_all_repos(repo_list, repo_features, username):
    for repo in repo_list:
        print(get_repo_stats(repo).name)
        repo_features.add_repo()
        if not repo.fork:
            process_entire_repo(repo, repo_features)
        else:
            repo_features.add_forked_repo()
            process_repo_commit_wise(repo, repo_features, username)


def main(username):
    github_obj = get_github_obj();
    try:
        user = get_user(github_obj, name=username)
    except UnknownObjectException:
        return {"issue": "InValid UserName"};

    repo_list = get_repos_list(user)
    repo_features = RepoFeatures()

    try:
        process_all_repos(repo_list, repo_features, username)
    except ValueError:
        # pass incomplete information, probably due to too many API CALLs
        pass

    concept_freq_table = process_all_keywords(repo_features.keywords)

    # print(repo_features.keywords)
    # best20keywords = get_top_keywords(concept_freq_table, 20)
    # print(best20keywords)

    mappings = load_mappings()
    concept_list = {}
    for keyword, freq in concept_freq_table.items():
        concept = find_concept(mappings, keyword)
        if concept is None:
            continue
        concept = concept.strip()

        if concept in concept_list:
            concept_list[concept] += freq
        else:
            concept_list[concept] = freq

    print(concept_list)
    repo_features.process_extension_to_percentages()
    concept_list = sorted(concept_list.items(), key=lambda item: item[1], reverse=True)
    if len(concept_list) <= 6:
        concept_list = dict(concept_list)
    else:
        concept_list = dict(concept_list[:6])

    to_return = {
        "concepts": concept_list,
        "extensions": repo_features.extensions,
        "TotalRepoCount": repo_features.totalRepos,
        "ForkedRepoCount": repo_features.forkedRepos
    }

    return to_return
