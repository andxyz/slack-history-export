a fork of https://gist.github.com/Chandler/fb7a070f52883849de35

_Note: The API calls were updated for the new `conversation` API, but the instructions below to get a token are outdated._

My fork is solely to document how to use the code with python3. If you are
unfamiliar with python3 but own a mac laptop.

The script finds all channels, private channels and direct messages
that your user participates in. it downloads the complete history for
those converations and writes each conversation out to seperate json files.

This user centric history gathering is nice because the official slack data exporter
only exports public channels.

PS, this only works if your slack team has a paid account which allows for unlimited history.

PPS, this use of the API is blessed by Slack.
https://get.slack.help/hc/en-us/articles/204897248

> If you want to export the contents of your own private groups and direct messages please see our API documentation.

- step 1 visit https://api.slack.com/docs/oauth-test-tokens and click "generate-test-token"

  ```shell
  open 'https://api.slack.com/docs/oauth-test-tokens'
  ```

- step 2 check https://api.slack.com/tokens

  ```shell
  open 'https://api.slack.com/tokens'
  ```

#### A simple usage example

```shell
cd slack-history-export/
brew install python3
pip3 install pipenv
pipenv --python=/usr/local/bin/python3 shell
pipenv install
pipenv run python slack_history.py --token='123token'
```

#### other usage examples

```shell
pipenv run python slack_history.py --token='123token'
pipenv run python slack_history.py --token='123token' --dryRun=True
pipenv run python slack_history.py --token='123token' --skipDirectMessages
pipenv run python slack_history.py --token='123token' --skipDirectMessages --skipPrivateChannels
```

see [./slack_history.py](slack_history.py)
