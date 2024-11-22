from collections import deque
import requests
import time
# import json
import os

# users = [
#     "jakubgania"
# ]

users_queue = deque(maxlen=10)
users_queue.append("jakubgania")

GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
# print(GITHUB_API_TOKEN)

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

def check_rate_limit():
    response = requests.get("https://api.github.com/rate_limit", headers={"Authorization": f"Bearer {GITHUB_API_TOKEN}"})
    data = response.json()
    remaining = data["resources"]["graphql"]["remaining"]
    reset_time = data["resources"]["graphql"]["reset"]
    return remaining, reset_time

def wait_for_reset(reset_time):
    sleep_time = reset_time - time.time()
    if sleep_time > 0:
        print(f"Rate limit exceeded. Waiting for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)

# def wait_for_reset(reset_time):
#     while True:
#         sleep_time = reset_time - time.time()
#         if sleep_time <= 0:
#             break  # Exit the loop once the reset time is reached
#         print(f"Rate limit exceeded. Waiting for {int(sleep_time)} seconds...", end="\r")
#         time.sleep(1)
#     print("Rate limit reset. Resuming requests...")

headers = {"Authorization": f"Bearer {GITHUB_API_TOKEN}"}
# response = requests.post("https://api.github.com/graphql", json={'query': QUERY, "variables": variables}, headers=headers)
# data = response.json()

output = []
# output_counter = 0
loop_counter = 0
# for username in users:
while loop_counter < 6:
    remaining, reset_time = check_rate_limit()
    if remaining == 0:
        wait_for_reset(reset_time)
    else:
        print(f"api rate limit: {remaining}")

    username = users_queue.popleft()

    variables = {
        "username": username
    }

    response = requests.post("https://api.github.com/graphql", json={'query': QUERY, "variables": variables}, headers=headers)
    data = response.json()
    # print(data)

    # if data and data

    if data and data["data"]["user"] is not None:
        organizations = data["data"]["user"]["organizations"]
        if organizations:
            if organizations["nodes"]:
                for item in organizations["nodes"]:
                    output.append(item["login"])
                    print("- - - - - - - - org")
                    print(item["login"])
                    print("- - - - - - - - org")
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
                    output.append(node["login"])
                    print(node["login"], node_followers_total_count, node_following_total_count)
                    if node_followers_total_count > 0 or node_following_total_count > 0:
                        users_queue.append(node["login"])
            else:
                print("followers nodes - empty")

            if followers["pageInfo"] and followers["pageInfo"]["hasNextPage"] == True:
                has_next_page = followers["pageInfo"]["hasNextPage"]
                cursor = followers["pageInfo"]["endCursor"]
                counter = 0

                while has_next_page and counter < 2:
                    variables_p = {
                        "username": username,
                        "cursor": cursor
                    }

                    response = requests.post("https://api.github.com/graphql", json={'query': PAGINATION_QUERY_FOLLOWERS, "variables": variables_p}, headers=headers)
                    data_p = response.json()
                    # print(data_p)

                    # if data_p["data"]["user"]["followers"]["totalCount"]:
                    #     print(data_p["data"]["user"]["followers"]["totalCount"])

                    nodes = data_p["data"]["user"]["followers"]["nodes"]
                    for node in nodes:
                        node_followers_total_count = node["followers"]["totalCount"]
                        node_following_total_count = node["following"]["totalCount"]
                        output.append(node["login"])
                        print(node["login"], node_followers_total_count, node_following_total_count)
                        if node_followers_total_count > 0 or node_following_total_count > 0:
                            users_queue.append(node["login"])

                    has_next_page = data_p["data"]["user"]["followers"]["pageInfo"]["hasNextPage"]
                    cursor = data_p["data"]["user"]["followers"]["pageInfo"]["endCursor"]

                    counter = counter + 1

                    print(has_next_page)
                    print(cursor)
                    print(counter)
            else:
                print("followers nextPage - no pagination")

            # if followers["totalCount"]:
            #     print(followers["totalCount"])


        following = data["data"]["user"]["following"]
        if following:
            if following["nodes"]:
                for node in following["nodes"]:
                    node_followers_total_count = node["followers"]["totalCount"]
                    node_following_total_count = node["following"]["totalCount"]
                    output.append(node["login"])
                    print(node["login"], node_followers_total_count, node_following_total_count)
                    if node_followers_total_count > 0 or node_following_total_count > 0:
                        users_queue.append(node["login"])
            else:
                print("following nodes - empty")

            if following["pageInfo"] and following["pageInfo"]["hasNextPage"] == True:
                has_next_page = following["pageInfo"]["hasNextPage"]
                cursor = following["pageInfo"]["endCursor"]
                counter = 0

                while has_next_page and counter < 2:
                    variables_p = {
                        "username": username,
                        "cursor": cursor
                    }

                    response = requests.post("https://api.github.com/graphql", json={'query': PAGINATION_QUERY_FOLLOWING, "variables": variables_p}, headers=headers)
                    data_p = response.json()
                    # print(data_p)

                    # if data_p["data"]["user"]["following"]["totalCount"]:
                    #     print(data_p["data"]["user"]["following"]["totalCount"])

                    nodes = data_p["data"]["user"]["following"]["nodes"]
                    for node in nodes:
                        node_followers_total_count = node["followers"]["totalCount"]
                        node_following_total_count = node["following"]["totalCount"]
                        output.append(node["login"])
                        print(node["login"], node_followers_total_count, node_following_total_count)
                        if node_followers_total_count > 0 or node_following_total_count > 0:
                            users_queue.append(node["login"])

                    has_next_page = data_p["data"]["user"]["following"]["pageInfo"]["hasNextPage"]
                    cursor = data_p["data"]["user"]["following"]["pageInfo"]["endCursor"]

                    counter = counter + 1

                    print(has_next_page)
                    print(cursor)
                    print(counter)
            else:
                print("following nextPage - no pagination")

            # if following["totalCount"]:
            #     print(following["totalCount"])
    else:
        print("this profile is an organization")

        organization = data["data"]["organization"]
        users_queue.append(organization["login"])
        print("- - - - - - - - org")
        print(organization["login"])
        print("- - - - - - - - org")

    if len(output) >= 10:
        print("10 or more than 10 items in output")
    else:
        print("less than 10 items in output")

    time.sleep(1)

    loop_counter = loop_counter + 1
    # for item in data["data"]["user"]["organizations"]["nodes"]:
    #     item = item["login"]
    #     print(item)

    # for item in data["data"]["user"]["followers"]["nodes"]:
    #     item = item["login"]
    #     print(item)

    # for item in data["data"]["user"]["following"]["nodes"]:
    #     item = item["login"]
    #     print(item)

# print(len(output))
output = list(set(output))
print(len(output))

# def print_duplicates(lst):
#     seen = set()
#     duplicates = set()
#     for item in lst:
#         if item in seen:
#             duplicates.add(item)
#         else:
#             seen.add(item)
#     print(duplicates)

# print_duplicates(output)

# json_string = json.dumps(data, indent=2)
# print(json_string)

