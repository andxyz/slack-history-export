from slacker import Slacker
import json
import argparse
import os

# do what kevin says
def listInterestingChannels(slack, dryRun):
  channels = slack.channels.list().body['channels']

  for channel in channels:
      if(channel['num_members'] > 2):
          print(channel['name'])

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='download slack history')

  parser.add_argument('--token', help="an api token for a slack user")

  parser.add_argument(
    '--dryRun',
    action='store_true',
    default=False,
    help="if dryRun is true, don't fetch/write history only get channel names")

  args = parser.parse_args()

  dryRun = args.dryRun

  slack = Slacker(args.token)

  listInterestingChannels(slack, dryRun)
