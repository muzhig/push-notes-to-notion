import json
import logging
import os
import time
import urllib
from urllib.parse import urlencode
from uuid import uuid4

import telegram
from telegram import Update
import sentry_init
import requests

from models import User

logger = logging.getLogger()
logger.setLevel(logging.INFO)

telegram_bot = telegram.Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])


def handle_telegram_push_to_notion(upd: Update):
    for user in User.telegram_chat_id_index.query(str(upd.message.chat_id)):
        try:
            user.push_to_notion(upd.message.text)
        except ValueError as ex:
            upd.message.reply_text(ex.args[0])
        break
    else:
        offer_to_connect_notion(upd)


def offer_to_connect_notion(upd: Update):
    upd.message.reply_text(
        f"Authorize notion first: https://ptn.potapov.dev"
    )


def telegram_webhook_handler(event: dict, context: dict) -> dict:
    logger.info(event['body'])
    upd = telegram.Update.de_json(json.loads(event['body']), telegram_bot)
    if upd.message and upd.message.text:
        if upd.message.text.startswith("/"):
            handle_command(upd)
        else:
            handle_telegram_push_to_notion(upd)
    return {
        "statusCode": 200,
        "body": json.dumps({})
    }


def handle_command(upd: Update):
    if upd.message.text.startswith("/start"):
        parts = upd.message.text.split(' ', 1)
        if len(parts) == 1:
            offer_to_connect_notion(upd)
        else:
            uuid = parts[1]
            try:
                user = User.get(uuid)
                for existing_user in User.telegram_chat_id_index.query(str(upd.message.chat_id)):
                    if existing_user.id == user.id:
                        continue
                    existing_user.telegram_chat_id = None
                    existing_user.save()
                    logger.info(f"Unlinked {existing_user.id} from chat_id {upd.message.chat_id}")
                user.telegram_chat_id = str(upd.message.chat_id)
                user.telegram_username = upd.message.from_user.username
                user.telegram_user_id = str(upd.message.from_user.id)
                user.last_updated = time.time()
                user.save()
                logger.info(f"Linked {user.id} to chat_id {upd.message.chat_id} / @{upd.message.from_user.username}")
                upd.message.reply_text("Telegram linked successfully")
            except User.DoesNotExist:
                upd.message.reply_text("Unknown Notion workspace id")
    else:
        upd.message.reply_text("¯\_(ツ)_/¯")


def notion_oauth(event: dict, context: dict) -> dict:
    client, secret = os.environ["NOTION_OAUTH_CLIENT_ID"], os.environ["NOTION_OAUTH_SECRET"]
    code = event["queryStringParameters"]["code"]
    raw_state = event["queryStringParameters"]["state"]
    state = json.loads(raw_state)
    resp = requests.post('https://api.notion.com/v1/oauth/token', json={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.environ["NOTION_OAUTH_REDIRECT_URI"],
        "state": raw_state
    }, auth=(client, secret)).json()

    access_token = resp["access_token"]
    bot_id = resp["bot_id"]
    owner = resp["owner"]
    owner_id = owner["user"]["id"]
    workspace_id = resp["workspace_id"]

    for user in User.notion_bot_index.query(resp["bot_id"]):
        user.notion_workspace_id = workspace_id
        user.notion_access_token = access_token
        user.notion_owner_id = owner_id
        user.notion_raw_oauth_response = json.dumps(resp)
        user.last_updated = time.time()
        user.save()
        logger.info(f"Refreshed token on existing user {user.id}")
        break
    else:
        user = User(
            id=str(uuid4()),
            notion_workspace_id=workspace_id,
            notion_owner_id=owner_id,
            notion_bot_id=bot_id,
            notion_access_token=access_token,
            notion_raw_oauth_response=json.dumps(resp),
            last_updated=time.time(),
            created=time.time(),
            expires=None
        )
        user.save()
        logger.info(f"Connected new Notion user {user.id}")
    redirect_url = state["return_url"] + f"?user={user.id}"
    return {
        "statusCode": 302,
        "headers": {
            "Location": redirect_url
        },
    }


def slack_oauth_handler(event: dict, context: dict) -> dict:
    client, secret = os.environ["SLACK_OAUTH_CLIENT_ID"], os.environ["SLACK_OAUTH_SECRET"]
    code = event["queryStringParameters"]["code"]
    raw_state = event["queryStringParameters"]["state"]
    state = json.loads(raw_state)
    resp = requests.post('https://slack.com/api/oauth.v2.access', data={
        "client_id": client,
        "client_secret": secret,
        "code": code,
        "redirect_uri": os.environ["SLACK_OAUTH_REDIRECT_URI"],
    }).json()
    logger.info(json.dumps(resp))
    team_id = resp["team"]["id"]
    team_name = resp["team"]["name"]

    bot_id = resp["bot_user_id"]
    bot_access_token = resp["access_token"]

    owner = resp["authed_user"]
    user_access_token = owner.get("access_token")
    user_id = owner["id"]

    user = User.get(state["user"])

    user.slack_team_id = team_id
    user.slack_team_name = team_name
    user.slack_bot_id = bot_id
    user.slack_bot_access_token = bot_access_token
    user.slack_user_id = user_id
    user.slack_user_access_token = user_access_token
    user.slack_raw_oauth_response = json.dumps(resp)
    user.last_updated = time.time()
    user.save()

    logger.info(f"Refreshed slack token on existing user {user.id}")

    redirect_url = state["return_url"] + f"?user={user.id}&slack=1"
    return {
        "statusCode": 302,
        "headers": {
            "Location": redirect_url
        },
    }


def parse_request(event):
    data = dict(event["queryStringParameters"] or {})
    lower_headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
    content_type = lower_headers.get("content-type")
    if content_type == "application/x-www-form-urlencoded":
        data.update(urllib.parse.parse_qsl(event["body"]))
    elif content_type and content_type.startswith("application/json"):
        data.update(json.loads(event["body"]))
    return data


def verify_slack_origin(request):
    app_verification_token = os.environ["SLACK_VERIFICATION_TOKEN"]
    token = request.get("token")
    if not token:
        logger.error("Missing token in slack webhook!")
        return False
    if token != app_verification_token:
        logger.error("Invalid verification token in slack webhook!")
        return False
    return True


def slack_webhook_handler(event: dict, context: dict) -> dict:
    request = parse_request(event)
    if not verify_slack_origin(request):
        return {
            "statusCode": 200
        }
    logger.info(event["body"])

    def send_from_user_id(notion_user: User, sender_id: str, text: str):
        if sender_id != user.slack_user_id:
            # todo: identify sender
            text = f'{text} (from @<{sender_id}>)'
        return notion_user.push_to_notion(text)

    if request.get("command"):
        try:
            user = User.slack_team_id_index.query(request["team_id"]).next()
            send_from_user_id(
                user,
                request["user_id"],
                request["text"]
            )
        except StopIteration:
            logger.error("Unknown user")
    elif request["type"] == "url_verification":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "challenge": request["challenge"]
            })
        }
    elif request["type"] == "event_callback":
        slack_event = request["event"]
        if slack_event["type"] in ("message", "app_mention"):
            try:
                user = User.slack_team_id_index.query(request["team_id"]).next()
                send_from_user_id(
                    user,
                    slack_event["user"],
                    slack_event["text"]
                )
            except StopIteration:
                logger.error("Unknown user")
    return {
        "statusCode": 201,
    }


def push_to_notion(event: dict, context: dict) -> dict:
    request = parse_request(event)
    user_id = request.get("user")
    if not user_id:
        return {
            "statusCode": 400,
            "body": "expected parameter: user"
        }
    try:
        user = User.get(user_id)
    except User.DoesNotExist:
        return {
            "statusCode": 404,
            "body": "Unknown user"
        }
    text = request.get("text")
    if not text and event["headers"].get("Content-Type") == "plain/text":
        text = event["body"]
    if not text:
        return {
            "statusCode": 400,
            "body": "expected parameter: text"
        }
    user.push_to_notion(text)
    return {
        "statusCode": 201,
    }
