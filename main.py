from github import Github
from github.GithubException import UnknownObjectException


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
        process_java_file(str(file.decoded_content, 'utf-8'), repo_features)
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
        print("PATH : " , path)
        if not has_valid_extension(path):
            continue
        allfiles.append(path)

    return allfiles

def process_repo_commit_wise(repo, repo_features, username):
    print(username)
    if not repo.name == "ip":
        return
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
            # pass
        else:
            repo_features.add_forked_repo()

        process_repo_commit_wise(repo, repo_features, username)

    print(repo_features.keywords)
    print(list(dict.fromkeys(repo_features.jarFilesUsed)))


if __name__ == "__main__":
    main()
