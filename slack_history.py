# MIT License

# Copyright (c) 2016 Chandler Abraham, 2022 Jérémie O. Lumbroso

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from slacker import Slacker
import json
import argparse
import os

# This script finds all channels, private channels and direct messages
# that your user participates in, downloads the complete history for
# those converations and writes each conversation out to seperate json files.
#
# This user centric history gathering is nice because the official slack data exporter
# only exports public channels.
#
# PS, this only works if your slack team has a paid account which allows for unlimited history.
#
# PPS, this use of the API is blessed by Slack.
# https://get.slack.help/hc/en-us/articles/204897248
# " If you want to export the contents of your own private groups and direct messages
# please see our API documentation."
#
# get your slack user token at the bottom of this page
# https://api.slack.com/web
#
# dependencies:
#  pip install slacker # https://github.com/os/slacker
#
# usage examples
#  python slack_history.py --token='123token'
#  python slack_history.py --token='123token' --dryRun=True
#  python slack_history.py --token='123token' --skipDirectMessages
#  python slack_history.py --token='123token' --skipDirectMessages --skipPrivateChannels --skipThreads


def getThread(channelId, threadTs, pageSize = 100):
  messages = []
  lastTimestamp = None

  while(True):
    response = slack.conversations.replies(
      channel = channelId,
      ts      = threadTs,
      latest  = lastTimestamp,
      oldest  = 0,
      limit   = pageSize
    ).body

    messages.extend(response['messages'])

    if (response['has_more'] == True):
      lastTimestamp = messages[-1]['ts'] # -1 means last element in a list
    else:
      break
  return messages

# fetches the complete message history for a channel/group/im
#
# pageableObject could be:
# slack.conversations
#
# channelId is the id of the channel/group/im you want to download history for.

def getHistory(pageableObject, channelId, pageSize = 100, get_threads = True):
  messages = []
  lastTimestamp = None

  while(True):
    response = pageableObject.history(
      channel = channelId,
      latest  = lastTimestamp,
      oldest  = 0,
      limit   = pageSize
    ).body

    msgs = response['messages']

    # see https://api.slack.com/messaging/retrieving#finding_threads
    for i in range(len(msgs)):
      if get_threads and 'thread_ts' in msgs[i]:
        threadTs = msgs[i]['thread_ts']
        if threadTs == msgs[i]['ts']:
          replies_data = getThread(channelId, threadTs)
          msgs[i]['replies'] = replies_data

    messages.extend(msgs)

    if (response['has_more'] == True):
      lastTimestamp = messages[-1]['ts'] # -1 means last element in a list
    else:
      break
  return messages

def mkdir(directory):
  if not os.path.exists(directory):
    os.makedirs(directory)

# fetch and write history for all public channels
def getChannels(slack, dryRun, get_threads = True):
  channels = slack.conversations.list(types="public_channel").body['channels']

  print("\nfound channels: ")
  for channel in channels:
    print(channel['name'])

  if not dryRun:
    parentDir = "channels"
    mkdir(parentDir)
    for channel in channels:
      print("getting history for channel {0}".format(channel['name']))
      fileName = "{parent}/{file}.json".format(parent = parentDir, file = channel['name'])
      messages = getHistory(slack.conversations, channel['id'], get_threads = get_threads)
      channelInfo = slack.conversations.info(channel['id']).body['channel']
      with open(fileName, 'w') as outFile:
        print("writing {0} records to {1}".format(len(messages), fileName))
        json.dump({'channel_info': channelInfo, 'messages': messages }, outFile, indent=4)

# fetch and write history for all direct message conversations
# also known as IMs in the slack API.
def getDirectMessages(slack, ownerId, userIdNameMap, dryRun, get_threads = True):
  dms = slack.conversations.list(types="im,mpim").body['channels']

  print("\nfound direct messages (1:1) with the following users:")
  
  for dm in dms:
    dm_recipient = dm["name"] if "name" in dm else dm["user"]
    print(userIdNameMap.get(dm_recipient, dm_recipient + " (name unknown)"))

  if not dryRun:
    parentDir = "direct_messages"
    mkdir(parentDir)
    for dm in dms:
      dm_recipient = dm["name"] if "name" in dm else dm["user"]
      name = userIdNameMap.get(dm_recipient, dm_recipient + " (name unknown)")
      print("getting history for direct messages with {0}".format(name))
      fileName = "{parent}/{file}.json".format(parent = parentDir, file = name)
      messages = getHistory(slack.conversations, dm['id'], get_threads = get_threads)
      channelInfo = {'members': [dm_recipient, ownerId]}
      with open(fileName, 'w') as outFile:
        print("writing {0} records to {1}".format(len(messages), fileName))
        json.dump({'channel_info': channelInfo, 'messages': messages}, outFile, indent=4)

# fetch and write history for all private channels
# also known as groups in the slack API.
def getPrivateChannels(slack, dryRun, get_threads = True):
  groups = slack.conversations.list(types="private_channel").body['channels']

  print("\nfound private channels:")
  for group in groups:
    print("{0}: ({1} members)".format(group['name'], group.get('num_members', 0)))

  if not dryRun:
    parentDir = "private_channels"
    mkdir(parentDir)

    for group in groups:
      messages = []
      print("getting history for private channel {0} with id {1}".format(group['name'], group['id']))
      fileName = "{parent}/{file}.json".format(parent = parentDir, file = group['name'])
      messages = getHistory(slack.conversations, group['id'], get_threads = get_threads)
      channelInfo = slack.conversations.info(group['id']).body['channel']
      with open(fileName, 'w') as outFile:
        print("writing {0} records to {1}".format(len(messages), fileName))
        json.dump({'channel_info': channelInfo, 'messages': messages}, outFile, indent=4)

# fetch all users for the channel and return a map userId -> userName
def getUserMap(slack):
  #get all users in the slack organization
  users = slack.users.list().body['members']
  userIdNameMap = {}
  for user in users:
    userIdNameMap[user['id']] = user['name']
  print("found {0} users ".format(len(users)))
  return userIdNameMap

# get basic info about the slack channel to ensure the authentication token works
def doTestAuth(slack):
  testAuth = slack.auth.test().body
  teamName = testAuth['team']
  currentUser = testAuth['user']
  print("Successfully authenticated for team {0} and user {1} ".format(teamName, currentUser))
  return testAuth

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='download slack history')

  parser.add_argument('--token', help="an api token for a slack user")

  parser.add_argument(
    '--dryRun',
    action='store_true',
    default=False,
    help="if dryRun is true, don't fetch/write history only get channel names")
  
  parser.add_argument(
    '--skipThreads',
    action='store_true',
    default=False,
    help="if skipThreads is true, don't fetch threads")

  parser.add_argument(
    '--skipPrivateChannels',
    action='store_true',
    default=False,
    help="skip fetching history for private channels")

  parser.add_argument(
    '--skipChannels',
    action='store_true',
    default=False,
    help="skip fetching history for public channels")
  
  parser.add_argument(
    '--skipAllChannels',
    action='store_true',
    default=False,
    help="skip fetching history for public & private channels")

  parser.add_argument(
    '--skipDirectMessages',
    action='store_true',
    default=False,
    help="skip fetching history for directMessages")

  args = parser.parse_args()

  slack = Slacker(args.token)

  testAuth = doTestAuth(slack)

  userIdNameMap = getUserMap(slack)

  dryRun = args.dryRun

  skipThreads = args.skipThreads

  if not dryRun:
    with open('metadata.json', 'w') as outFile:
      print("writing metadata")
      metadata = {
        'auth_info': testAuth,
        'users': userIdNameMap
      }
      json.dump(metadata, outFile, indent=4)

  if not args.skipAllChannels and not args.skipChannels:
    getChannels(slack, dryRun, get_threads = not skipThreads)

  if not args.skipAllChannels and not args.skipPrivateChannels:
    getPrivateChannels(slack, dryRun, get_threads = not skipThreads)

  if not args.skipDirectMessages:
    getDirectMessages(slack, testAuth['user_id'], userIdNameMap, dryRun, get_threads = not skipThreads)
