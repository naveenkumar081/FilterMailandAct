from dataclasses import dataclass
from datetime import datetime

class GCPOAuthDetails:
    SCOPES_FOR_GMAIL = ["https://www.googleapis.com/auth/gmail.modify",
                        'https://www.googleapis.com/auth/gmail.readonly']
    AUTH_URI =  "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URI =  "https://oauth2.googleapis.com/token"
    CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"

@dataclass
class MailDetails:
    id: str
    from_address: str
    to_address: str
    thread_id: str
    sent_time: datetime
    subject: str
    labels: str
    mail_read: bool
    mail_snippet: str

@dataclass()
class LabelDetails:
    id: str
    name: str
    type: str


@dataclass
class TokenData:
    refresh_token: str
    expire_time: datetime
    user_id: str


class MailClassifications:
    UNREAD = "UNREAD"
    READ = "READ"
    FROM_ADDRESS = "From"
    SUBJECT = "Subject"
    DELIVERED_TO = "Delivered-To"
    DATE = "Date"
    RECEIVED  = "Received"

class TableAdapters:
    MailDetails = "mail_details"
    TokenDetails = "token_details"
    LabelDetails = "label_details"


class HTMLForTable:
    html_content =  """
    <html>
    <head>
        <title>Email Details</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h2>Email Details</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>From Address</th>
                <th>Thread ID</th>
                <th>Sent Time</th>
                <th>Subject</th>
                <th>Labels</th>
                <th>Mail Read</th>
                <th>Mail Snippet</th>
            </tr>
    """