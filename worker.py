from collections import deque
from termcolor import colored
from enum import Enum
import requests
import json
import time
import os

# class StorageType(Enum):
#     REDIS = "redis"
#     QUEUE = "queue"

# CURRENT_STORAGE = StorageType.QUEUE

config = {
    "mainLoop": {
        "limitNumberOfLoops": True,
        "limitCounter": 2
    },
    "followersPaginationLoops": {
        "limitNumberOfLoops": False,
        "limitCounter": 1
    },
    "followingsPaginationLoops": {
        "limitNumberOfLoops": False,
        "limitCounter": 1
    }
}

users_fetched = deque()

users_queue = deque(maxlen=100)
users_queue.append("jakubgania")

GITHUB_RATE_LIMIT_ENDPOINT = "https://api.github.com/rate_limit"
GITHUB_API_ENDPOINT = "https://api.github.com/graphql"
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_API_TOKEN}"}
MAIN_LOOP_TIME_SLEEP = 1.4
PAGINATION_LOOP_TIME_SLEEP = 1.8

QUERY = """
query($username: String!) {
    user(login: $username) {
        login
        name
        organizations(first: 100) {
            nodes {
                name
                login
            }
        }
        followers(first: 100) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
                name
                login
                followers {
                    totalCount
                }
                following {
                    totalCount
                }
            }
            totalCount
        }
        following(first: 100) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
                name
                login
                followers {
                    totalCount
                }
                following {
                    totalCount
                }
            }
            totalCount
        }
    }
}
"""

PAGINATION_QUERY_FOLLOWERS = """
query($username: String!, $cursor: String!) {
    user(login: $username) {
        followers(first: 100, after: $cursor) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
                name
                login
                followers {
                    totalCount
                }
                following {
                    totalCount
                }
            }
            totalCount
        }
    }
}
"""

PAGINATION_QUERY_FOLLOWING = """
query($username: String!, $cursor: String!) {
    user(login: $username) {
        following(first: 100, after: $cursor) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
                name
                login
                followers {
                    totalCount
                }
                following {
                    totalCount
                }
            }
            totalCount
        }
    }
}
"""

def fetch_api_data(query, variables, headers):
    try:
        response = requests.post(
            GITHUB_API_ENDPOINT,
            json={
                'query': query,
                'variables': variables
            },
            headers=headers
        )

        response.raise_for_status()
    
        data = response.json()
        if 'errors' in data:
            print(" ")
            print(colored("GraphQL query error", 'red'))
            print(colored(data["errors"][0]["message"], 'red'))
            print(" ")
            
            return []

        return response
    except requests.exceptions.HTTPError as http_err:
        print(colored(f"HTTP error occurred: {http_err}", 'red'))
        return []

def get_rate_limit():
    response = requests.get(GITHUB_RATE_LIMIT_ENDPOINT, headers = HEADERS)
    data = response.json()
    remaining = data["resources"]["graphql"]["remaining"]
    reset_time = data["resources"]["graphql"]["reset"]
    return remaining, reset_time

def wait_for_reset(reset_time):
    sleep_time = reset_time - time.time()
    if sleep_time > 0:
        print(f"Rate limit exceeded. Waiting for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)

def check_rate_limit():
    remaining, reset_time = get_rate_limit()
    if remaining == 0:
        wait_for_reset(reset_time)
    else:
        print(" ")
        print(colored(f"api rate limit: {remaining}", 'light_yellow'))

# def wait_for_reset(reset_time):
#     while True:
#         sleep_time = reset_time - time.time()
#         if sleep_time <= 0:
#             break  # Exit the loop once the reset time is reached
#         print(f"Rate limit exceeded. Waiting for {int(sleep_time)} seconds...", end="\r")
#         time.sleep(1)
#     print("Rate limit reset. Resuming requests...")

output = []
# output_counter = 0
main_loop_counter = 0
total_number_of_fetched_logins = 0

while True:
    if config["mainLoop"]["limitNumberOfLoops"] and config["mainLoop"]["limitCounter"] <= main_loop_counter:
        break

    check_rate_limit()

    users_fetched_set = set(users_fetched)

    print(" ")
    print(colored("fetched usernames:", 'light_green'))
    print(" ")
    for item in users_fetched_set:
        print(colored(f"* {item}", 'light_yellow'))

    # username = users_queue.popleft()
    username = ""
    
    unique_username = None
    while users_queue:
        username = users_queue.popleft()
        if username not in users_fetched_set:
            unique_username = username
            break
        else:
            print(f"{username} already exists in users_fetched. Skipping.")

    if unique_username:
        print(f"Unique username found: {unique_username}")
        username = unique_username
    else:
        print("No unique usernames available in users_queue.")

    temp_output = []

    print(" ")
    print(colored(f"getting data for user: {username}", 'blue'))
    print(" ")

    variables = {
        "username": username
    }

    # response = requests.post(GITHUB_API_ENDPOINT, json={'query': QUERY, "variables": variables}, headers=headers)
    response = fetch_api_data(QUERY, variables, HEADERS)
    data = []

    if response:
        data = response.json()

    if data and data["data"]["user"] is not None:
        organizations = data["data"]["user"]["organizations"]
        if organizations:
            if organizations["nodes"]:
                for item in organizations["nodes"]:
                    temp_output.append(item["login"])
                    print("- - - - - - - -")
                    print(item["login"])
                    print("- - - - - - - -")
            else:
                print("organizaions nodes - empty")

        followers = data["data"]["user"]["followers"]
        if followers:
            hasNextPage = False
            endCursor = ""

            if followers["nodes"]:
                for node in followers["nodes"]:
                    node_followers_total_count = node["followers"]["totalCount"]
                    node_following_total_count = node["following"]["totalCount"]
                    temp_output.append(node["login"])
                    print(node["login"], node_followers_total_count, node_following_total_count)

                    # detailed log
                    # print(colored(f"for:          {username}", 'green'))
                    # print("- - - - - - - - - - - - - - - - - - - - - - - - ")
                    # print(colored(f"login:        {node['login']}", 'green'))
                    # print("- - - - - - - - - - - - - - - - - - - - - - - - ")
                    # print(colored(f"followers:    {node_followers_total_count}", 'green'))
                    # print("- - - - - - - - - - - - - - - - - - - - - - - - ")
                    # print(colored(f"following:    {node_following_total_count}", 'green'))
                    # print("- - - - - - - - - - - - - - - - - - - - - - - - ")
                    # print(colored(f"total:        {node_followers_total_count + node_following_total_count}", 'green'))
                    # print("- - - - - - - - - - - - - - - - - - - - - - - - ")
                    # print(colored(f"kind:         follower", 'green'))
                    # print(" ")
                    # print(colored("===============================================", 'cyan'))
                    # print(" ")

                    if node_followers_total_count > 0 or node_following_total_count > 0:
                        users_queue.append(node["login"])
            else:
                print("followers nodes - empty")

            if followers["pageInfo"] and followers["pageInfo"]["hasNextPage"]:
                has_next_page = followers["pageInfo"]["hasNextPage"]
                cursor = followers["pageInfo"]["endCursor"]
                followersPaginationCounter = 0

                while has_next_page:
                    if config["followersPaginationLoops"]["limitNumberOfLoops"] and config["followersPaginationLoops"]["limitCounter"] <= followersPaginationCounter:
                        break

                    check_rate_limit()

                    variables_query_followers = {
                        "username": username,
                        "cursor": cursor
                    }

                    print(" ")
                    print(colored("pagination query", 'light_red'))
                    print(colored("type:      followers", 'light_red'))
                    print(colored(f"username:  {username}", 'light_red'))
                    print(colored(f"cursor:    {cursor}", 'light_red'))
                    print(" ")

                    response = requests.post(
                        GITHUB_API_ENDPOINT,
                        json = {
                            'query': PAGINATION_QUERY_FOLLOWERS,
                            "variables": variables_query_followers
                        },
                        headers = HEADERS
                    )
                    data_p = response.json()

                    nodes = data_p["data"]["user"]["followers"]["nodes"]
                    for node in nodes:
                        node_followers_total_count = node["followers"]["totalCount"]
                        node_following_total_count = node["following"]["totalCount"]
                        temp_output.append(node["login"])
                        print(node["login"], node_followers_total_count, node_following_total_count)
                        if node_followers_total_count > 0 or node_following_total_count > 0:
                            users_queue.append(node["login"])

                    has_next_page = data_p["data"]["user"]["followers"]["pageInfo"]["hasNextPage"]
                    cursor = data_p["data"]["user"]["followers"]["pageInfo"]["endCursor"]

                    followersPaginationCounter = followersPaginationCounter + 1

                    # print(has_next_page)
                    # print(cursor)
                    # print(followersPaginationCounter)
                    print("")
                    print(colored(f"followers pagination counter {followersPaginationCounter}", 'light_blue'))
                    print(" ")
                    print(colored("time sleep - followers loop", 'light_yellow'))

                    time.sleep(PAGINATION_LOOP_TIME_SLEEP)
            else:
                print(" ")
                print(colored("followers nextPage - no pagination", 'light_magenta'))
                print(" ")

        following = data["data"]["user"]["following"]
        if following:
            if following["nodes"]:
                for node in following["nodes"]:
                    node_followers_total_count = node["followers"]["totalCount"]
                    node_following_total_count = node["following"]["totalCount"]
                    temp_output.append(node["login"])
                    print(node["login"], node_followers_total_count, node_following_total_count)
                    if node_followers_total_count > 0 or node_following_total_count > 0:
                        users_queue.append(node["login"])
            else:
                print("following nodes - empty")

            if following["pageInfo"] and following["pageInfo"]["hasNextPage"]:
                has_next_page = following["pageInfo"]["hasNextPage"]
                cursor = following["pageInfo"]["endCursor"]
                followingPaginationCounter = 0

                while has_next_page:
                    if config["followingsPaginationLoops"]["limitNumberOfLoops"] and config["followingsPaginationLoops"]["limitCounter"] <= followingPaginationCounter:
                        break

                    check_rate_limit()

                    variables_query_following = {
                        "username": username,
                        "cursor": cursor
                    }

                    print(" ")
                    print(colored("pagination query", 'light_red'))
                    print(colored("type:      following", 'light_red'))
                    print(colored(f"username:  {username}", 'light_red'))
                    print(colored(f"cursor:    {cursor}", 'light_red'))
                    print(" ")

                    response = requests.post(
                        GITHUB_API_ENDPOINT,
                        json = {
                            'query': PAGINATION_QUERY_FOLLOWING,
                            "variables": variables_query_following
                        },
                        headers = HEADERS
                    )
                    data_p = response.json()

                    nodes = data_p["data"]["user"]["following"]["nodes"]
                    for node in nodes:
                        node_followers_total_count = node["followers"]["totalCount"]
                        node_following_total_count = node["following"]["totalCount"]
                        temp_output.append(node["login"])
                        print(node["login"], node_followers_total_count, node_following_total_count)
                        if node_followers_total_count > 0 or node_following_total_count > 0:
                            users_queue.append(node["login"])

                    has_next_page = data_p["data"]["user"]["following"]["pageInfo"]["hasNextPage"]
                    cursor = data_p["data"]["user"]["following"]["pageInfo"]["endCursor"]

                    followingPaginationCounter = followingPaginationCounter + 1

                    # print(has_next_page)
                    # print(cursor)
                    # print(followingPaginationCounter)
                    print(" ")
                    print(colored(f"followers pagination counter {followingPaginationCounter}", 'light_blue'))
                    print(" ")
                    print(colored("time sleep - following loop", 'light_yellow'))

                    time.sleep(PAGINATION_LOOP_TIME_SLEEP)
            else:
                print(" ")
                print(colored("following nextPage - no pagination", 'light_magenta'))
                print(" ")

        output.extend(temp_output)
        users_fetched.append(username)
    else:
        print("this profile is an organization")
        print("the initial value for username can't be an organization")

        if len(output) == 0:
            exit()

        # the code below doesn't work because the query doesn't retrieve this data
        # organization = data["data"]["organization"]
        # users_queue.append(organization["login"])
        # print("- - - - - - - - org")
        # print(organization["login"])
        # print("- - - - - - - - org")

    print(colored("time sleep - main loop", 'light_yellow'))
    time.sleep(MAIN_LOOP_TIME_SLEEP)
    
    print(" ")
    print(colored(f"main loop counter: {main_loop_counter}", 'light_grey'))
    print(" ")
    
    main_loop_counter = main_loop_counter + 1
    total_number_of_fetched_logins = total_number_of_fetched_logins + len(temp_output)
    
    print(f"fetched logins in this loop: {len(temp_output)}")
    print(f"total number of fetched logins: {total_number_of_fetched_logins}")

    output = list(set(output))
    number_of_unique_logins = len(output)
    print(f"total number of unique logins: {number_of_unique_logins}")

output = list(set(output))
number_of_unique_logins = len(output)
print(f"total number of unique logins: {number_of_unique_logins}")
