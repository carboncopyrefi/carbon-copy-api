# CARBON Copy API

The CARBON Copy API is designed to communicate with external data sources and serve content to a front end.

There is also a function that updates impact metrics stored in our database.

## Looking for the CARBON Copy data?

Reach out at hello@carboncopy.news.

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

