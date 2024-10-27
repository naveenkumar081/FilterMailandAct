# This file is intended to list the mail under a mailbox and store it in the database
# !/usr/bin/env python3
import sys
import os
from datetime import datetime
from typing import Any
from oslo_config import cfg

possible_top_dir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                os.pardir,
                                                os.pardir))
if os.path.exists(os.path.join(possible_top_dir, 'FilterandAct', '__init__.py')):
    sys.path.insert(0, possible_top_dir)

from common import config
from common.definitions import MailDetails
from common.definitions import MailClassifications
from common import google_utils
from common import utils
from common import database_adapter

from common.definitions import TableAdapters
from common.definitions import LabelDetails


class MailParser:
    def __init__(self):
        self.google_client = google_utils.instance.get_gcp_token_with_auth_code()
        if not self.google_client:
            raise Exception("Could not fetch Google token. Please check your configs.")

        if self.google_client.expired:
            self.google_client = google_utils.instance.refresh_existing_token(self.google_client)

    @staticmethod
    def update_label_details(message: dict[str, Any],
                      /) -> tuple[bool, str]:
        is_message_unread = False
        updated_label_format  = ""
        labels_for_the_message = message.get('labelIds', [])
        if MailClassifications.UNREAD in labels_for_the_message:
            is_message_unread = True

        for each_label in labels_for_the_message:
            updated_label_format += f",{each_label}"

        return is_message_unread, updated_label_format

    @staticmethod
    def parse_details_from_headers(message: dict[str, Any],
                                   /) -> tuple[str, str, str, datetime]:
        message_headers = message.get('payload', {}).get('headers', [])
        subject = from_address = to_address =  ""
        received_date = None
        for specific_headers in message_headers:
            header_name  = specific_headers.get('name')
            header_value = specific_headers.get("value")
            if header_name == MailClassifications.FROM_ADDRESS:
                from_address = utils.extract_email(header_value) or ""

            if header_name == MailClassifications.DELIVERED_TO:
                to_address = header_value

            if header_name == MailClassifications.SUBJECT:
                subject = header_value

            if header_name == MailClassifications.DATE:
                received_date = utils.parse_time_object_from_string(header_value)

        return subject, from_address, to_address, received_date

    def parse_mail_details(self,
                           /) -> list[MailDetails]:

        list_of_messages = google_utils.instance.list_mail_from_the_id()

        masked_message_list = []

        for message in list_of_messages:
            if detailed_message := google_utils.instance.get_detailed_message(message):
                is_message_un_read, updated_label_message = self.update_label_details(detailed_message)
                subject, from_address, to_address, received_date = self.parse_details_from_headers(detailed_message)
                masked_message = MailDetails(id=detailed_message.get('id'),
                                             mail_snippet=detailed_message.get('snippet'),
                                             thread_id=detailed_message.get('threadId'),
                                             subject=subject,
                                             from_address=from_address,
                                             sent_time=received_date,
                                             labels=updated_label_message,
                                             mail_read=not is_message_un_read,
                                             to_address=to_address
                                             )
                masked_message_list.append(masked_message)

        return masked_message_list

    @staticmethod
    def parse_label_details() -> list[LabelDetails]:

        list_of_labels = google_utils.instance.list_labels_for_the_user()

        final_label_list = []

        for detailed_label in list_of_labels:
            masked_label = LabelDetails(id=detailed_label.get('id'),
                                        name=detailed_label.get('name'),
                                        type=detailed_label.get('type')
                                        )
            final_label_list.append(masked_label)

        return final_label_list

    def parse_mail_and_store(self):
        masked_message_list = self.parse_mail_details()
        database_adapter.instance.create_table_from_dataclass(MailDetails, TableAdapters.MailDetails,
                                                              primary_key="id")
        database_adapter.instance.update_table_with_dataclass_list(masked_message_list, TableAdapters.MailDetails)

    @staticmethod
    def parse_label_and_store():
        label_list = MailParser.parse_label_details()
        database_adapter.instance.create_table_from_dataclass(LabelDetails, TableAdapters.LabelDetails, primary_key='id')
        database_adapter.instance.update_table_with_dataclass_list(label_list, TableAdapters.LabelDetails)


if __name__ == '__main__':
    cfg.CONF(project='ParseMail', version='1.0.0', prog='ParseMail')
    print("Sanity Check has been initiated..")
    config.startup_sanity_checks()
    print("Sanity Check has been passed")
    parser = MailParser()
    print("Started Parsing Labels")
    parser.parse_label_and_store()
    print("completed parsing Labels")
    parser.parse_mail_and_store()
    print("Completed Storing Mails")
