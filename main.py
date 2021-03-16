from github import Github
from github.GithubException import UnknownObjectException
import threading


# ==============================================================================
# CLASSES
# ==============================================================================

class RepoFeatures:
    def __init__(self):
        self.name = None
        self.java_lines = 0
        self.keywords = {}
        self.jarFilesUsed = []
        self.forkedRepos = 0
        self.repo_stars = {}
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


# ==============================================================================
# FUNCTIONS
# ==============================================================================

def has_valid_extension(path):
    if "." not in path:
        return True
    else:
        valid_extensions = [".java", ".jar"]

        for ext in valid_extensions:
            if path.endswith(ext):
                return True

    return False


def get_repos_list(user):
    return user.get_repos()


def get_github_obj():
    with open("accesstoken.txt", "r") as reader:
        access_token = str(reader.readline()).strip()
    g = Github(access_token)
    return g


def get_user(github_obj, name):
    return github_obj.get_user(name)


def get_repo_stats(repo):
    rf = RepoFeatures()
    rf.set_name(repo.name)
    return rf


def process_java_file(file_content, repo_features):
    lines = file_content.split("\n")
    for line in lines:
        line.strip()
        if line.startswith("import"):
            line = line[len("import "):]
            if line.strip().startswith("java") or line.strip().startswith("org"):
                repo_features.add_keyword(line.strip())


def process_file(file, repo_features):
    if file.name.endswith("java"):
        threading.Thread(target=process_java_file, args=(str(file.decoded_content, 'utf-8'), repo_features, ))
        # process_java_file(str(file.decoded_content, 'utf-8'), repo_features)
    elif file.name.endswith("jar"):
        repo_features.add_jar(file.name)


def process_repo_recursively(repo, repo_features, current_path, src_found=False, dir_depth_count=0):
    if src_found is False and dir_depth_count > 3:
        return
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
        return

    for file in contents:
        if file.type == "dir":
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


def get_all_files_from_commit(repo, repo_features, commit):
    allfiles = []
    for file in commit.files:
        path = file.filename
        print("PATH : ", path)
        if not has_valid_extension(path):
            continue
        allfiles.append(path)

    return allfiles


def process_repo_commit_wise(repo, repo_features, username):
    print(username)
    all_commits = repo.get_commits(author=username)
    print(all_commits.totalCount)
    all_files = []
    for commit in all_commits:
        all_files = all_files + get_all_files_from_commit(repo, repo_features, commit)

    all_files = list(dict.fromkeys(all_files))
    for file in all_files:
        try:
            actual_file = repo.get_contents(file)
            process_file(actual_file, repo_features)
        except:
            """Essentially to deal with deletion"""
            pass


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
    with open("framework-feature.csv", "r") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split(",")
            mappings[parts[0]] = parts[1]

    return mappings


def find_concept(mappings, keyword):
    for phrase, concept in mappings.items():
        if phrase in keyword:
            return concept
    return keyword


def main():
    github_obj = get_github_obj();
    username = "rajobasu"
    user = get_user(github_obj, name=username)
    repo_list = get_repos_list(user)
    repo_features = RepoFeatures()
    for repo in repo_list:
        print(get_repo_stats(repo).name)

        if not repo.fork:
            process_entire_repo(repo, repo_features)
        else:
            repo_features.add_forked_repo()
            process_repo_commit_wise(repo, repo_features, username)

    print(repo_features.keywords)
    concept_freq_table = process_all_keywords(repo_features.keywords)
    best20keywords = get_top_keywords(concept_freq_table, 20)
    print(best20keywords)

    mappings = load_mappings()
    conceptList = {}
    for keyword, freq in concept_freq_table.items():
        concept = find_concept(mappings, keyword).strip()
        if concept in conceptList:
            conceptList[concept] += freq
        else:
            conceptList[concept] = freq

    print(conceptList)
    print(list(dict.fromkeys(repo_features.jarFilesUsed)))


if __name__ == "__main__":
    main()
