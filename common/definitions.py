from dataclasses import dataclass
from datetime import datetime

class GCPOAuthDetails:
    AUTH_URI =  "https://accounts.google.com/o/oauth2/auth"
    CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
    SCOPES_FOR_GMAIL = ["https://www.googleapis.com/auth/gmail.modify",
                        'https://www.googleapis.com/auth/gmail.readonly']
    TOKEN_URI =  "https://oauth2.googleapis.com/token"


@dataclass
class MailDetails:
    from_address: str
    id: str
    labels: str
    mail_read: bool
    mail_snippet: str
    sent_time: datetime
    subject: str
    thread_id: str
    to_address: str

@dataclass()
class LabelDetails:
    id: str
    name: str
    type: str


@dataclass
class TokenData:
    expire_time: datetime
    refresh_token: str
    user_id: str


class MailClassifications:
    DELIVERED_TO = "Delivered-To"
    DATE = "Date"
    FROM_ADDRESS = "From"
    READ = "READ"
    RECEIVED  = "Received"
    SUBJECT = "Subject"
    UNREAD = "UNREAD"


class TableAdapters:
    LabelDetails = "label_details"
    MailDetails = "mail_details"
    TokenDetails = "token_details"


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