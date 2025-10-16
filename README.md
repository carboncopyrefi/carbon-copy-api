# CARBON Copy API

The CARBON Copy API is designed to communicate with external data sources and serve content to a front end.

There is also a function that updates impact metrics stored in our database.

## Endpoints

Host: api.carboncopy.news

- /projects - Get all projects in the CARBON Copy database
- /projects/{project_slug} - Get static data for a specific project
- /projects/{project_slug}/content - Get dynamic data for a specific project
- /projects/categories/{category_slug} - Get category profile data
- /projects/categories/tokens - Get tokens issued by projects in a specific category
- /people - Get list of builders in the ReFi space
- /news - Get list of recent news items
- /feed - Generates an XML of all ReFi news items
- /knowledge - Get list of resources created by ReFi projects

## Want to fork?

You'll need Python 3.10 and pip installed before installing the packages in requirements.txt.

You'll also need to do two things:

### Create keys.py

They current version of keys.py has the following keys if you want all functionality:

- WARPCAST_KEY - the private key of the Farcaster account you want to post with
- DUNE_KEY - your Dune API Key
- COINGECKO_KEY - your CoinGecko API key
- BASEROW_TOKEN - your Baserow API token with READ access for all tables
- SURVEY_ACCESS_TOKEN - the token that allows a front-end to send post requests to the API
- IMPACT_METRICS_BASEROW_TOKEN - your Baserow API token with WRITE access
- SUBGRAPH_API_KEY - your subgraph API key

### Edit config.py file

The current version is tailored for the Baserow open-source database platform, so the config.py keys are mostly related to that. Update the keys as required.

