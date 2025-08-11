#!/etc/icinga2/scripts/python-env/bin/python

import argparse

import mattermostdriver

import config

def connect_to_mattermost() -> tuple[mattermostdriver.Driver, str]:
    mattermost = mattermostdriver.Driver(
        {
            "url": config.MATTERMOST_URL,
            "token": config.MATTERMOST_TOKEN,
            "port": config.MATTERMOST_PORT,
        }
    )

    mattermost.login()
    channel_id = mattermost.channels.get_channel_by_name_and_team_name(
        config.MATTERMOST_TEAM, config.MATTERMOST_CHANNEL
    )["id"]
    return (mattermost, channel_id)


def post_alert(payload):
    mattermost, channel = connect_to_mattermost()

    # If the payload is for an attachment, it needs to be inside 'props'
    final_payload = {
        'channel_id': channel,
        'props': payload
    }

    # If we need a message field (for @channel), it should be at the top level
    if 'message' in payload:
        final_payload['message'] = payload.pop('message')

    mattermost.posts.create_post(final_payload)

def parse_args():
    parser = argparse.ArgumentParser(description="Format Icinga service notification for Mattermost")

    # Required parameters
    parser.add_argument("-d", "--datetime", required=True, help="Long date time")
    parser.add_argument("-l", "--hostname", required=True, help="Host name")
    parser.add_argument("-n", "--hostdisplayname", required=True, help="Host display name")
    parser.add_argument("-o", "--output", required=True, help="Service output")
    parser.add_argument("-s", "--state", required=True, help="Service state")
    parser.add_argument("-t", "--notificationtype", required=True, help="Notification type")

    # Optional parameters
    parser.add_argument("-4", "--hostaddress", help="IPv4 address")
    parser.add_argument("-6", "--hostaddress6", help="IPv6 address")
    parser.add_argument("-X", "--hostnotes", help="Host notes")
    parser.add_argument("-x", "--servicenotes", help="Service notes")
    parser.add_argument("-b", "--author", help="Notification author")
    parser.add_argument("-c", "--comment", help="Notification comment")
    parser.add_argument("-i", "--icingaurl", help="Icinga Web 2 URL")
    parser.add_argument("-e", "--servicename", help="Service name (optional for host notifications)")
    parser.add_argument("-u", "--servicedisplayname", help="Service display name (optional for host notifications)")


    return parser.parse_args()

COLORS = {
    "OK": "#00FF00",       # Green for OK
    "WARNING": "#FFFF00",  # Yellow for WARNING
    "CRITICAL": "#FF0000", # Red for CRITICAL
    "UNKNOWN": "#808080",  # Gray for UNKNOWN
    "UP": "#00FF00",       # Green for UP
    "DOWN": "#FF0000",     # Red for DOWN
}


def format_message(args):
    alert_color = COLORS.get(args.state.upper(), "#808080")  # Default to gray
    if args.servicename:
        # Service notification
        lines = [
            f"**{args.notificationtype}**: `{args.state}`",
            f"**Service**: {args.servicedisplayname} on `{args.hostdisplayname}`",
            f"**Output**: {args.output}",
            f"**Time**: {args.datetime}",
        ]
    else:
        # Host notification
        lines = [
            f"**{args.notificationtype}**: `{args.state}`",
            f"**Host**: {args.hostdisplayname}",
            f"**Output**: {args.output}",
            f"**Time**: {args.datetime}",
        ]

    if args.comment:
        lines.append(f"**Comment**: _{args.comment}_")
    if args.author:
        lines.append(f"**Author**: {args.author}")
    if args.icingaurl:
        lines.append(f"[View in Icinga]({args.icingaurl})")

    lines.append("***")
    payload = {
        'message': '',
        'attachments': [
            {
                'color': alert_color,
                'text': "\n".join(lines)
            }
        ]
    }

    if args.state.upper() not in ["OK", "UP"]:
        payload['message'] = "@channel"

    return payload
if __name__ == "__main__":
    args = parse_args()
    message = format_message(args)
    post_alert(message)  # Replace with Mattermost post logic later
