import os
import sys

from unittest import mock

from common.definitions import MailClassifications
from common.definitions import LabelDetails
from scripts.fetch_mail_and_store import MailParser


possible_top_dir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                os.pardir,
                                                os.pardir))
if os.path.exists(os.path.join(possible_top_dir, 'FilterandAct', '__init__.py')):
    sys.path.insert(0, possible_top_dir)

def test_update_label_details_with_unread():
    # Test when the message has the "UNREAD" label
    message = {"labelIds": [MailClassifications.UNREAD, "INBOX", "IMPORTANT"]}

    # Expected output
    expected_is_unread = True
    expected_label_format = ",UNREAD,INBOX,IMPORTANT"

    is_unread, label_format = MailParser.update_label_details(message)

    assert is_unread == expected_is_unread
    assert label_format == expected_label_format


def test_update_label_details_without_unread():
    # Test when the message does not have the "UNREAD" label
    message = {"labelIds": ["INBOX", "IMPORTANT"]}

    # Expected output
    expected_is_unread = False
    expected_label_format = ",INBOX,IMPORTANT"

    is_unread, label_format = MailParser.update_label_details(message)

    assert is_unread == expected_is_unread
    assert label_format == expected_label_format


def test_update_label_details_empty_labels():
    # Test when the message has no labels
    message = {"labelIds": []}

    # Expected output
    expected_is_unread = False
    expected_label_format = ""

    is_unread, label_format = MailParser.update_label_details(message)

    assert is_unread == expected_is_unread
    assert label_format == expected_label_format


def test_update_label_details_missing_labelIds_key():
    # Test when the message dictionary does not contain 'labelIds' key
    message = {}

    # Expected output
    expected_is_unread = False
    expected_label_format = ""

    is_unread, label_format = MailParser.update_label_details(message)

    assert is_unread == expected_is_unread
    assert label_format == expected_label_format


def test_parser_values_from_headers():
    # Test when the message has the "UNREAD" label
    message = {"payload": {
        "headers": [{'name': 'Delivered-To', 'value': 'devnaveenklingam@gmail.com'},
        {'name': 'Received', 'value': 'by 2002:a05:6a20:45d:b0:1cc:df2f:1163 with SMTP id b29csp188501pzb;        Wed, 23 Oct 2024 01:27:40 -0700 (PDT)'},
                              {'name': 'Date', 'value': 'Wed, 23 Oct 2024 01:27:39 -0700'},
                    {'name': 'Reply-To', 'value': 'Google Business Profile <businessprofile-noreply@google.com>'},
 {'name': 'Message-ID', 'value': '<696aa6bdf072a6dbfaaa50b74c8f8b93e1a9fb80-20077711-111072481@google.com>'},
                    {'name': 'Subject', 'value': 'Important: Your business isn’t showing on Google. Verify now'},
                    {'name': 'From', 'value': 'Google Business Profile <businessprofile-noreply@google.com>'},
                    {'name': 'To', 'value': 'devnaveenklingam@gmail.com'},
                    {'name': 'Content-Type', 'value': 'multipart/alternative; boundary="000000000000af65bb062520a80e"'}]
    }}

    # Expected output
    expected_subject = "Important: Your business isn’t showing on Google. Verify now"
    expected_from_address = "businessprofile-noreply@google.com"
    expected_to_address = "devnaveenklingam@gmail.com"

    subject, from_address, to_address, received_date = MailParser.parse_details_from_headers(message)

    assert subject == expected_subject
    assert from_address == expected_from_address
    assert to_address == expected_to_address


def test_parser_values_from_headers_with_mail_id_alone_in_from():
    message = { "payload": {
        "headers": [{'name': 'Delivered-To', 'value': 'devnaveenklingam@gmail.com'},
                    {'name': 'Received',
                     'value': 'by 2002:a05:6a20:45d:b0:1cc:df2f:1163 with SMTP id b29csp188501pzb;        Wed, 23 Oct 2024 01:27:40 -0700 (PDT)'},
                    {'name': 'Date', 'value': 'Wed, 23 Oct 2024 01:27:39 -0700'},
                    {'name': 'Reply-To', 'value': 'Google Business Profile <businessprofile-noreply@google.com>'},
                    {'name': 'Message-ID',
                     'value': '<696aa6bdf072a6dbfaaa50b74c8f8b93e1a9fb80-20077711-111072481@google.com>'},
                    {'name': 'Subject', 'value': 'Important: Your business isn’t showing on Google. Verify now'},
                    {'name': 'From', 'value': 'businessprofile-noreply@google.com'},
                    {'name': 'To', 'value': 'devnaveenklingam@gmail.com'},
                    {'name': 'Content-Type', 'value': 'multipart/alternative; boundary="000000000000af65bb062520a80e"'}]
    }
    }

    expected_subject = "Important: Your business isn’t showing on Google. Verify now"
    expected_from_address = "businessprofile-noreply@google.com"
    expected_to_address = "devnaveenklingam@gmail.com"

    subject, from_address, to_address, received_date = MailParser.parse_details_from_headers(message)

    assert subject == expected_subject
    assert from_address == expected_from_address
    assert to_address == expected_to_address




def test_parser_values_from_headers_for_non_spl_characters():
    message ={ "payload": {
        "headers": [
                    {'name': 'Subject', 'value': 'Important: Your business isn’t showing on Google. Verify now'},
                    {'name': 'From', 'value': 'businessprofilenoreply@google.com'},
                    {'name': 'Delivered-To', 'value': 'devnaveenklingam@gmail.com'},
                    {'name': 'Content-Type', 'value': 'multipart/alternative; boundary="000000000000af65bb062520a80e"'}]
    }
    }
    expected_subject = "Important: Your business isn’t showing on Google. Verify now"
    expected_from_address = "businessprofilenoreply@google.com"
    expected_to_address = "devnaveenklingam@gmail.com"
    expected_received_date = None
    subject, from_address, to_address, received_date = MailParser.parse_details_from_headers(message)

    assert subject == expected_subject
    assert from_address == expected_from_address
    assert to_address == expected_to_address
    assert received_date == expected_received_date


def test_parser_values_from_headers_for_empty_response():
    message = { "payload": {
        "headers": [
        ]
    }}
    expected_subject = ""
    expected_from_address = ""
    expected_to_address = ""
    expected_received_date = None
    subject, from_address, to_address, received_date = MailParser.parse_details_from_headers(message)

    assert subject == expected_subject
    assert from_address == expected_from_address
    assert to_address == expected_to_address
    assert received_date == expected_received_date

