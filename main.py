from github import Github


class RepoFeatures:
    def __init__(self):
        self.name = None
        self.java_lines = 0
        self.keywords = []
        pass

    def set_name(self, name):
        self.name = name

    def add_java_lines(self, lines):
        self.java_lines += lines

    def add_keyword(self, keyword):
        self.keywords.append(keyword)

    def add_keywords(self, keywords):
        self.keywords = self.keywords + keywords


def get_repos_list(user):
    return user.get_repos()


def get_github_obj():
    with open("accesstoken.txt", "r") as reader:
        accesstoken = str(reader.readline()).strip()
    g = Github(accesstoken)
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
            if line.strip().startswith("java"):
                parts = line.split(".")
                repo_features.add_keywords(parts)


def process_repo_recursively(repo, repo_features, current_path, src_found=False, dir_depth_count=0):
    if src_found is False and dir_depth_count > 3:
        return

    contents = repo.get_contents(current_path)
    for file in contents:
        if file.type == "dir":
            if file.name == "src":
                process_repo_recursively(repo, repo_features,file.path, True, dir_depth_count + 1)
            else:
                process_repo_recursively(repo, repo_features,file.path, src_found, dir_depth_count + 1)
        else:
            if file.name.endswith("java"):
                # print(str(file.decoded_content, 'utf-8'))
                process_java_file(str(file.decoded_content, 'utf-8'), repo_features)


def process_repo(repo, repo_stats):
    print("-" *40)
    print(repo.name)
    process_repo_recursively(repo,repo_stats, "")
    print("-" *40)


def main():
    github_obj = get_github_obj();
    user = get_user(github_obj, name="rajobasu")
    repo_list = get_repos_list(user)
    repo_features = RepoFeatures()
    for repo in repo_list:
        print(get_repo_stats(repo).name)
        if repo.name == "ip":
            process_repo(repo, repo_features)
    print(list(dict.fromkeys(repo_features.keywords)))



if __name__ == "__main__":
    main()
