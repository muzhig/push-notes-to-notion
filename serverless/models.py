import json
import logging

import requests
from requests import Session
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection


logger = logging.getLogger()


class TelegramChatIdIndex(GlobalSecondaryIndex):
    class Meta:
        # index_name is optional, but can be provided to override the default name
        index_name = 'UserByTelegramChatId'
        # All attributes are projected
        projection = AllProjection()

    telegram_chat_id = UnicodeAttribute(hash_key=True)


class NotionBotIdIndex(GlobalSecondaryIndex):
    class Meta:
        # index_name is optional, but can be provided to override the default name
        index_name = 'UserByNotionBot'
        # All attributes are projected
        projection = AllProjection()

    notion_bot_id = UnicodeAttribute(hash_key=True)


class SlackTeamIdIndex(GlobalSecondaryIndex):
    class Meta:
        # index_name is optional, but can be provided to override the default name
        index_name = 'UserBySlackTeamId'
        # All attributes are projected
        projection = AllProjection()

    slack_team_id = UnicodeAttribute(hash_key=True)


class User(Model):
    class Meta:
        table_name = "ptn-users"
    id = UnicodeAttribute(hash_key=True)
    telegram_chat_id = UnicodeAttribute(null=True)
    telegram_user_id = UnicodeAttribute(null=True)
    telegram_username = UnicodeAttribute(null=True)
    telegram_chat_id_index = TelegramChatIdIndex()
    notion_workspace_id = UnicodeAttribute(null=True)
    notion_bot_id = UnicodeAttribute(null=True)
    notion_bot_index = NotionBotIdIndex()
    notion_owner_id = UnicodeAttribute(null=True)
    notion_access_token = UnicodeAttribute(null=True)
    notion_raw_oauth_response = UnicodeAttribute(null=True)
    slack_team_id = UnicodeAttribute(null=True)
    slack_team_id_index = SlackTeamIdIndex()
    slack_team_name = UnicodeAttribute(null=True)
    slack_user_id = UnicodeAttribute(null=True)
    slack_username = UnicodeAttribute(null=True)
    slack_user_access_token = UnicodeAttribute(null=True)
    slack_bot_id = UnicodeAttribute(null=True)
    slack_bot_access_token = UnicodeAttribute(null=True)
    slack_raw_oauth_response = UnicodeAttribute(null=True)
    last_updated = NumberAttribute(null=True)
    created = NumberAttribute(null=True)
    expires = NumberAttribute(null=True)

    def session(self) -> Session:
        if not hasattr(self, "_notion_session"):
            self._notion_session = requests.session()
            self._notion_session.headers = {
                "Authorization": f"Bearer {self.notion_access_token}",
                "Notion-Version": "2022-06-28"
            }
        return self._notion_session

    def get_primary_page(self) -> dict:
        pages = self.session().post('https://api.notion.com/v1/search', json={
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            }
        }).json()['results']
        if len(pages) == 0:
            raise ValueError("No access to any page")
        elif len(pages) > 1:
            raise ValueError("More than one page is accessible, ignoring")
        return pages[0]

    def push_to_notion(self, text: str) -> dict:
        page = self.get_primary_page()
        ses = self.session()
        resp = ses.patch(f'https://api.notion.com/v1/blocks/{page["id"]}/children', json={
            "children": [{
                "type": "to_do",
                "to_do": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": text,
                        }
                    }],
                    "checked": False,
                    "color": "default",
                }
            }]
        }).json()
        logger.info(json.dumps(resp))
        return resp
