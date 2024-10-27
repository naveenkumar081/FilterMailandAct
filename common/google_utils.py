from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from oslo_config import cfg
from common.definitions import GCPOAuthDetails
from common import utils
from common.definitions import TableAdapters
from common.definitions import TokenData
from common import database_adapter
from datetime import datetime
from typing import Optional
from typing import Any


class GoogleClientFetcher:
    def __init__(self,
                 /) -> None:
        self.__client_config = {cfg.CONF.mail_config.app_type: {
            "client_id": cfg.CONF.mail_config.client_id,
            "client_secret": cfg.CONF.mail_config.client_secret,
            "project_id": cfg.CONF.mail_config.project_id,
            "auth_uri": GCPOAuthDetails.AUTH_URI,
            "token_uri": GCPOAuthDetails.TOKEN_URI
        }}
        self.__auth_code = utils.url_parse(cfg.CONF.mail_config.authorization_code)

    @staticmethod
    def refresh_generated_token_to_table(creds: Credentials,
                                         /) -> None:
        refresh_token = creds.refresh_token
        expires_in = creds.expiry
        expires_in = expires_in.replace(microsecond=0)
        set_clause_to_pass = f"refresh_token='{refresh_token}', expire_time='{expires_in}', user_id='{cfg.CONF.mail_config.project_id}'"
        database_adapter.instance.upsert_data_in_table(TableAdapters.TokenDetails, set_clause_to_pass)

    def get_gcp_token_with_auth_code(self,
                                     /) -> Credentials:
        query_to_fetch_account_details = f"user_id='{cfg.CONF.mail_config.project_id}';"
        database_adapter.instance.create_table_from_dataclass(TokenData, TableAdapters.TokenDetails,
                                                              primary_key="user_id")
        token_details_for_the_account = database_adapter.instance.select_table(TableAdapters.TokenDetails,
                                                                               where=query_to_fetch_account_details)
        if token_details_for_the_account:
            refresh_token = token_details_for_the_account[0].get("refresh_token")
            expired_time = token_details_for_the_account[0].get("expire_time")
            if datetime.now() >= expired_time:
                creds = GoogleClientFetcher().refresh_google_token(refresh_token=refresh_token)
                GoogleClientFetcher.refresh_generated_token_to_table(creds)

            else:
                creds = Credentials(
                    None,
                    refresh_token=refresh_token,
                    client_id=cfg.CONF.mail_config.client_id,
                    client_secret=cfg.CONF.mail_config.client_secret,
                    token_uri=GCPOAuthDetails.TOKEN_URI
                )
            return creds

        flow = InstalledAppFlow.from_client_config(self.__client_config, GCPOAuthDetails.SCOPES_FOR_GMAIL,
                                                   redirect_uri=cfg.CONF.mail_config.redirect_uris)

        flow.fetch_token(code=self.__auth_code)

        creds = flow.credentials

        GoogleClientFetcher.refresh_generated_token_to_table(creds)

        return creds

    @staticmethod
    def refresh_existing_token(creds: Credentials,
                               /) -> Credentials:
        return creds.refresh(Request())

    @staticmethod
    def refresh_google_token(refresh_token):
        # Create credentials from the refresh token
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=cfg.CONF.mail_config.client_id,
            client_secret=cfg.CONF.mail_config.client_secret,
            token_uri=GCPOAuthDetails.TOKEN_URI
        )

        # Refresh the access token
        creds.refresh(Request())

        # Access the new token
        return creds

    def list_mail_from_the_id(self,
                              /,
                              *,
                              creds: Credentials = None) -> list[str]:
        if not creds:
            creds = self.get_gcp_token_with_auth_code()

        service = build("gmail", "v1", credentials=creds)
        list_of_mails = service.users().messages().list(userId=cfg.CONF.mail_parser.mail_parse).execute()
        final_ids_list = [each_mail.get("id") for each_mail in list_of_mails.get("messages", [])]
        return final_ids_list

    def update_labels_for_the_mail(self,
                                   message_id: str,
                                   /,
                                   *,
                                   labels_to_add: list[str] = None,
                                   labels_to_remove: list[str] = None,
                                   creds: Credentials = None) -> None:
        if not creds:
            creds = self.get_gcp_token_with_auth_code()

        body_json = {}
        if labels_to_add:
            body_json["addLabelIds"] = labels_to_add

        if labels_to_remove:
            body_json["removeLabelIds"] = labels_to_remove

        service = build("gmail", "v1", credentials=creds)
        service.users().messages().modify(userId=cfg.CONF.mail_parser.mail_parse,
                                          id=message_id,
                                          body=body_json
                                          ).execute()

    def get_detailed_message(self,
                             msg_id: str,
                             /,
                             *,
                             creds: Credentials = None) -> Optional[dict[str, Any]]:
        if not creds:
            creds = self.get_gcp_token_with_auth_code()

        service = build("gmail", "v1", credentials=creds)
        message_details = service.users().messages().get(userId=cfg.CONF.mail_parser.mail_parse,
                                                         id=msg_id).execute()
        return message_details

    def list_labels_for_the_user(self,
                                 /,
                                 *,
                                 creds: Credentials = None) -> list[dict[str, Any]]:
        if not creds:
            creds = self.get_gcp_token_with_auth_code()

        service = build("gmail", "v1", credentials=creds)
        list_of_labels = service.users().labels().list(userId=cfg.CONF.mail_parser.mail_parse).execute()
        return list_of_labels.get("labels", [])


instance: Optional[GoogleClientFetcher] = None
