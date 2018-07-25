import sys
import time
import re
import rollbar
from slackclient import SlackClient
from ecs_deploy import handle_ecs_bot_cmd
from secret_manager import get_secret

# logging
import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# constants
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
COMMAND_REGEX = "^(?P<cmd>\w+)\s(to)\s(?P<cluster>\w+)\s(?P<services>(([a-zA-Z0-9\/\-]+)(\:([a-zA-Z0-9\-]+))?)?(\,([a-zA-Z0-9\/\-]+)(\:([a-zA-Z0-9\-]+)){1})*)$"
SERVICES_REGEX = "(?P<service>[a-zA-Z0-9\/\-]+)(\:(?P<tag>[a-zA-Z0-9\-]+))?"


def parse_bot_commands(starterbot_id, slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def parse_command(message_text):
    m = re.search(COMMAND_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    if not m:
        raise ValueError

    services = []
    for svc in re.finditer(SERVICES_REGEX, m.group("services")):
        services.append({"service": svc.group("service"), "tag": svc.group("tag")})

    return (m.group("cmd"), m.group("cluster"), services) if m else (None, None, None)


def handle_command(slack_client, authorized_channel_id, command, channel):
    """
        Executes bot command if the command is known
    """

    parameters = {
        "channel": channel,
        "text": "Not sure what you mean. Try *{}*" \
                .format("@nysa deploy to <cluster> <service>:<tag>[,<service>:<tag>] or @nysa deploy all:<tag>")
    }

    if channel != authorized_channel_id:
        parameters["text"] = "you cannot invoke @nysa outside of the authorized channel"
    else:
        try:
            parameters.update(handle_ecs_bot_cmd(*parse_command(command)))
        except ValueError:
            pass
        except Exception as ex:
            logging.error(ex)
            rollbar.report_exc_info(sys.exc_info())
            parameters["text"] = "Oops, there was an error with the deploy, try it again!!"

    # Sends the response back to the channel
    slack_client.api_call("chat.postMessage", **parameters)


if __name__ == "__main__":

    logging.info("Starting Slackbot")
    rollbar.init(get_secret('ROLLBAR_KEY'))
    authorized_channel = get_secret('SLACK_BOT_AUTHORIZED_CHANNEL')
    slack_client = SlackClient(get_secret('SLACK_BOT_TOKEN'))

    try:

        logging.info("getting channels list")
        rs = slack_client.api_call("channels.list")
        channels = [channel for channel in rs.get(u'channels')]
        logging.info("getting private groups list")
        rs = slack_client.api_call("groups.list")
        channels.extend([group for group in rs.get(u'groups')])

        authorized_channel_id = next(channel for channel in channels
                                     if channel.get(u'name').lower() == authorized_channel.lower()).get(u'id')

        logging.info("connecting to rtm")
        if slack_client.rtm_connect(with_team_state=False):
            logging.info("Starter Bot connected and running!")
            # Read bot's user ID by calling Web API method `auth.test`
            starterbot_id = slack_client.api_call("auth.test")["user_id"]
            while True:
                command, channel = parse_bot_commands(starterbot_id, slack_client.rtm_read())
                if command:
                    handle_command(slack_client, authorized_channel_id, command, channel)
                time.sleep(RTM_READ_DELAY)
        else:
            logging.error("Connection failed. Exception traceback printed above.")
    except Exception as e:
        logging.error(e)
        rollbar.report_exc_info()

