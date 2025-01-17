# Importing modules
import sys
import os
import colors
import Logo
import argparse

# Getting the name of the repository.
def getting_header(soup_text):
    title = soup_text.title.get_text()

    start = title.find('/')
    stop = title.find(':')
    return title[start + 1: stop]


# Function to make sure all the Url passed is made in particualr format.
def format_url(url):
    if url.startswith('http://'):
        url = url.replace('http', 'https')
    elif url.startswith('www.'):
        url = url.replace('www.', 'https://')
    elif url.startswith('https://') or url.startswith('https://www.'):
        pass
    else:
        colors.error("Enter the repositories url in given format"
                     "[ https://github.com/username/repository_name ]")
        sys.exit(1)
    return url


# Function to verify that the page URL given
# is pointing to some repository or not.
def verify_url(page_data):
    data = str(page_data)
    if "Popular repositories" in data:
        return False
    elif "Page not found" in data:
        return False
    else:
        return True


# Function returning email of the stargazer
def get_latest_commit(repo_name, username):
    email = ""
    commit_data = requests.get(
                "https://github.com"
                "/{}/{}/commits?author={}".format(
                                                 username,
                                                 repo_name,
                                                 username)).text
    soup = BeautifulSoup(commit_data, "lxml")
    a_tags = soup.findAll("a")
    for a_tag in a_tags:
        URL = a_tag.get("href")
        if URL.startswith("/{}/{}/commit/".format(username, repo_name)):
            label = str(a_tag.get("aria-label"))
            if "Merge" not in label and label != "None":
                patch_data = requests.get("https://github.com{}{}".format(
                            URL, ".patch")).text
                try:
                    start = patch_data.index("<")
                    stop = patch_data.index(">")
                    email = patch_data[start + 1: stop]
                except ValueError:
                    return "Not enough information."
                break
    if email != "":
        return email
    else:
        return "Not enough information."


def email(repository_link,ver,save):
    try:
        import data
    except ImportError:
        colors.error('Error importing data module')
        sys.exit(1)

    try:
        # Getting HTML page of repository
        html = requests.get(repository_link, timeout=8).text
    except (requests.exceptions.RequestException,
            requests.exceptions.HTTPError):
        colors.error(
            "Enter the repositories url in given format "
            "[ https://github.com/username/repository_name ]")
        sys.exit(1)
    # Checking if the url given is of a repository or not.
    result = verify_url(html)
    if result:
        colors.success("Got the repository data ", verbose)
    else:
        colors.error("Please enter the correct URL ")
        sys.exit(0)
    # Parsing the html data using BeautifulSoup
    soup1 = BeautifulSoup(html, "lxml")
    title = getting_header(soup1)  # Getting the title of the page
    data.header = title  # Storing title of the page as Project Title
    colors.success("Repository Title : " + title, verbose)
    colors.process("Doxing started ...\n", verbose)
    stargazer_link = repository_link + "/stargazers"
    while (stargazer_link is not None):
        stargazer_html = requests.get(stargazer_link).text
        soup2 = BeautifulSoup(stargazer_html, "lxml")
        a_next = soup2.findAll("a")
        for a in a_next:
            if a.get_text() == "Next":
                stargazer_link = a.get('href')
                break
            else:
                stargazer_link = None
        follow_names = soup2.findAll("h3", {"class": "follow-list-name"})
        for name in follow_names:
            a_tag = name.findAll("a")
            username = a_tag[0].get("href")
            data.username_list.append(username[1:])
    count = 1
    pos = 0
    while(count <= len(data.username_list)):
        repo_data = requests.get(
            "https://github.com/{}?tab=repositories&type=source"
            .format(data.username_list[pos])).text
        repo_soup = BeautifulSoup(repo_data, "lxml")
        a_tags = repo_soup.findAll("a")
        repositories_list = []
        for a_tag in a_tags:
            if a_tag.get("itemprop") == "name codeRepository":
                repositories_list.append(a_tag.get_text().strip())
        if len(repositories_list) > 0:
            email = get_latest_commit(
                    repositories_list[0],
                    data.username_list[pos])  # Getting stargazer's email
            data.email_list.append(str(email))
        else:
            data.email_list.append("Not enough information.")
        count += 1
        pos += 1

    # Printing or saving the emails
    print(colors.red + "{0}".format("-") * 75, colors.green, end="\n\n")
    save_data = False
    for arg in sys.argv[1:]:
        if arg == '-s' or arg == '--save':
            save_data = True
            save_info(dat='emails')
    if save_data is False:
        for e in range(len(data.email_list)):
            print(colors.white)
            print(data.username_list[e], (30-len(data.username_list[e]))*' ',
                  colors.green, '::',
                  colors.white, data.email_list[e])
    print("\n", colors.green + "{0}".format("-") * 75,
          colors.green, end="\n\n")


def save_info(dat='stardox'):
    try:
        import data
        import csv
    except ImportError:
        colors.error('Error importing data module')
        sys.exit(1)

    if dat == 'stardox':
        fields = ['Username', 'Repositories', 'Stars', 'Followers',
                  'Following', 'Email']
        rows = [[0 for x in range(6)] for y in range(len(data.username_list))]
        for row in range(len(data.username_list)):
            rows[row][0] = '@' + data.username_list[row]
            rows[row][1] = data.repo_list[row].strip()
            rows[row][2] = data.star_list[row].strip()
            rows[row][3] = data.followers_list[row].strip()
            rows[row][4] = data.following_list[row].strip()
            rows[row][5] = data.email_list[row]
    elif dat == 'emails':
        fields = ['Username', 'Email']
        rows = [[0 for x in range(2)] for y in range(len(data.username_list))]
        for row in range(len(data.username_list)):
            rows[row][0] = '@' + data.username_list[row]
            rows[row][1] = data.email_list[row]

    file_path = args.save
    if file_path is not None and file_path.endswith('.csv'):
        pass
    else:
        csv_file = data.header + '.csv'  # Name of csv file
        file_path = os.path.join(os.environ["HOME"], "Desktop", csv_file)
    try:
        with open(file_path, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            csvwriter.writerows(rows)
            colors.success("Saved the data into " + file_path, True)
    except FileNotFoundError:
        colors.error("Please enter valid path.")
        sys.exit()


def get_closed_issue(repository_link):
    '''
    Get total issues by repo link
    '''
    req_url = repository_link + "/issues"

    try:
        # Getting HTML page of repository
        html = requests.get(req_url, timeout=80).text
    except (requests.exceptions.RequestException,
            requests.exceptions.HTTPError):
        print("Enter the repositories url in given format ")
        print("[ https://github.com/username/repository_name ]")
        sys.exit(1)
    # Checking if the url given is of a repository or not.
    result = verify_url(html)
    if result:
        pass
    else:
        colors.error("Please enter the correct URL ")
        sys.exit(0)
    # Parsing the html data using BeautifulSoup
    soup1 = BeautifulSoup(html, "lxml")
    try:
        import data
    except ImportError:
        colors.error('Error importing data module')
        sys.exit(1)

    issue_closed_span = soup1.find("a", {"data-ga-click": "Issues, Table state, Closed"})
    issue_closed_value = issue_closed_span.get_text().strip().split(" ")[0]

    return int(issue_closed_value.strip())

def percentage(part, whole):
  p = float(part)/float(whole)
  return "{:.1%}".format(p)

def stardox(repo_link, ver, save):
    '''
    Succ: print result in one line
    Error: print multi lines
    '''
    try:
        print_data = True
        save_data = False
        for arg in sys.argv[1:]:
            if arg == '-s' or arg == '--save':
                save_data = True
                print_data = False

        repository_link = repo_link
        verbose = ver
        try:
            # Getting HTML page of repository
            html = requests.get(repository_link, timeout=80).text
        except (requests.exceptions.RequestException,
                requests.exceptions.HTTPError):
            print("Enter the repositories url in given format ")
            print("[ https://github.com/username/repository_name ]")
            sys.exit(1)
        # Checking if the url given is of a repository or not.
        result = verify_url(html)
        if result:
            pass
            #colors.success("Got the repository data ", verbose)
        else:
            colors.error("Please enter the correct URL ")
            sys.exit(0)
        # Parsing the html data using BeautifulSoup
        soup1 = BeautifulSoup(html, "lxml")
        try:
            import data
        except ImportError:
            colors.error('Error importing data module')
            sys.exit(1)
        title = getting_header(soup1)  # Getting the title of the page
        data.header = title  # Storing title of the page as Project Title
        #colors.success("Repository Title : " + title, verbose)
        star_value = watch_value = fork_value = 0

        print_info=""

        # Find issues
        issue_closed_value = 0
        issue_opened_value = 0
        issue_total_value = 0
        pull_value = 0

        issue_opened_span = soup1.find("span", {"id": "issues-repo-tab-count"})
        issue_opened_value = int(issue_opened_span.get_text().strip())

        issue_closed_value = get_closed_issue(repository_link)
        issue_total_value = issue_closed_value + issue_opened_value

        pull_span = soup1.find("span", {"id": "pull-requests-repo-tab-count"})
        pull_value = pull_span.get_text()


        closed_rate = percentage(issue_closed_value, issue_total_value)

        print_info += ("Opened Issues/Total Issues : " + str(issue_opened_value) + "/" + str(issue_total_value))
        print_info += (", closed rate " + closed_rate)
        print_info += (". PR Opened : " + pull_value)


        # Find stargazers
        stargazers_span = soup1.find("span", {"id": "repo-stars-counter-star"})
        star_value = stargazers_span["title"]

        fork_span = soup1.find("span", {"id": "repo-network-counter"})
        fork_value = fork_span["title"]

        print_info += (". Total stargazers : " + star_value)
        print_info += (". Total Forks : " + fork_value)

        print(print_info)

    except BaseException as e:
        print("\n\nError..!\nThanks for using :)")
        print(e)
        sys.exit(0)


if __name__ == '__main__':
    try:
        #Logo.header()  # For Displaying Logo

        parser = argparse.ArgumentParser()
        parser.add_argument('-r', '--rURL', help=" Path to repository.",
                            required=False, default=False)
        parser.add_argument('-v', '--verbose', help="Verbose",
                            required=False, default=True,
                            action='store_false')
        parser.add_argument('-s', '--save',
                            help="Save the doxed data in a csv file."
                                 " By default, saved at Desktop.",
                            required=False, default="../Desktop")
        parser.add_argument('-e', '--email', action='store_true',
                            help="Fetch only emails of stargazers.",
                            required=False, default=False)

        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            print('Error importing requests module.')
            print("Install by requirements.txt first.")
            sys.exit(1)

        args = parser.parse_args()
        repository_link = args.rURL
        verbose = args.verbose
        issave = args.save
        isemail = args.email


        if args.rURL == False:
            repository_link = input(
                        "\033[37mEnter the repository address :: \x1b[0m")
            print(repository_link)

        repository_link = format_url(repository_link)
        if isemail:
            email(repository_link,verbose,issave)
        else:
            stardox(repository_link,verbose,issave)

    except KeyboardInterrupt:
        print("\n\nYou're Great..!\nThanks for using :)")
        sys.exit(0)
