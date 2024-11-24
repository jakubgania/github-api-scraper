# github-api-scraper

A script that allows scraping data from the GitHub GraphQL API.

1. Clone the repository:
```bash
git clone https://github.com/jakubgania/github-api-scraper.git

cd github-api-scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

In this case, the script only collects user logins because I needed such data for my other project.

You need to generate an API token in your GitHub account and provide an initial value from which the script will start collecting data.

You can also use your own username if your number of followers or following is greater than zero.

You can set the script's behavior in the config variable. If the "limitNumberOfLoops" field is set to False, the script will run forever or until the end of the pagination is encountered. If the value is set to True, the script will execute the specified number of cycles in the "limitCounter" field.

Currently, the script does not save the results from the API anywhere, it only prints them to the terminal.

You can modify the script to suit your needs.

The script is still in development.

Useful links:

[About the GraphQL API](https://docs.github.com/en/graphql/overview/about-the-graphql-api)

[GitHub GraphQL API documentation](https://docs.github.com/en/graphql)

[Exploring GraphQL API queries](https://docs.github.com/en/graphql/overview/explorer)

[Objects in GraphQL represent the resources you can access](https://docs.github.com/en/graphql/reference/objects)

[Rate limits and node limits for the GraphQL API](https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api)

