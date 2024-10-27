import datetime
import re

from dateutil.relativedelta import relativedelta
from typing import Optional

from urllib import parse

from common import time_utils
from common.definitions import HTMLForTable

def match_string(pattern: str,
                 string: str,
                 /,
                 *,
                 match_type: str ='equal'):
    if match_type == 'equals to':
        regex = f"^{re.escape(pattern)}$"

    elif match_type == 'contains':
        regex = re.escape(pattern)
    else:
        raise ValueError("match_type must be 'equal' or 'contains'")

    return bool(re.search(regex, string))


def extract_time_value_and_unit(input_string: str,
                                /) -> tuple[Optional[int], Optional[str]]:
    value = unit = None
    pattern = r"(\d+)\s*(minutes?|hours?|Days|months?)"

    match = re.search(pattern, input_string)

    if match:
        value = int(match.group(1))
        unit = match.group(2)

    return value, unit

def extract_email(email_address_to_search: str,
                  /) ->  Optional[str]:
    if not email_address_to_search:
        return None

    if '<' not in email_address_to_search:
        return email_address_to_search

    email_pattern = r'<(.*?)>'
    match = re.search(email_pattern, email_address_to_search)
    if match:
        return match.group(1)
    else:
        return None


def parse_time_object_from_string(string_value_of_time: str,
                                  /) -> datetime:
    match = re.search(r'(\w{3}, \d{1,2} \w{3} \d{4} \d{2}:\d{2}:\d{2} [-+]\d{4})', string_value_of_time)
    date_str = match.group(1)

    local_datetime = time_utils.convert_string_to_date(date_str)

    native_converted_time =  time_utils.convert_to_utc_naive(local_datetime)

    return native_converted_time.replace(microsecond=0)


def update_time_values_based_on_the_result(predicated_time: str,
                                           to_compare_date: datetime,
                                           /,
                                           *,
                                           predicate_value: str = "equals to") -> bool:

    time_unit, value_of_the_unit = extract_time_value_and_unit(predicated_time)
    if not value_of_the_unit:
        return False

    predicate_value_in_lower_case = predicate_value.lower()

    time_unit_in_lower_case = value_of_the_unit.lower()

    current_time = datetime.datetime.now()
    if time_unit_in_lower_case  == "hours":
        time_to_replace = current_time - relativedelta(hour=time_unit)

    elif time_unit_in_lower_case == "days":
        time_to_replace = current_time - relativedelta(day=time_unit)

    elif time_unit_in_lower_case == "months":
        time_to_replace = current_time - relativedelta(month=time_unit)

    elif time_unit_in_lower_case == "minutes":
        time_to_replace = current_time - relativedelta(month=time_unit)

    else:
        time_to_replace = None

    if not time_to_replace:
        return False

    value_to_check = time_utils.compare(to_compare_date, time_to_replace)

    if predicate_value_in_lower_case == "equals to" and value_to_check == 0:
        return True

    if predicate_value_in_lower_case == "greater than" and value_to_check == 1:
        return True

    if predicate_value_in_lower_case == "less than" and value_to_check == -1:
        return True

    return False


def url_parse(string_to_parse: str,
              /) -> str:
    parsed_string = parse.unquote_plus(string_to_parse)
    return parsed_string


def convert_comma_delimited_to_list(string_to_convert: str,
                                    /) -> list[str]:
    comma_delimited_ = string_to_convert.split(',')
    if '' in comma_delimited_:
        comma_delimited_.remove('')

    return comma_delimited_


def save_data_as_html_table(data_list,
                            /) ->  None:
    html_content = HTMLForTable.html_content

    for data in data_list:
        html_content += f"""
            <tr>
                <td>{data.get('id', '')}</td>
                <td>{data.get('from_address', '')}</td>
                <td>{data.get('thread_id', '')}</td>
                <td>{data.get('sent_time', '')}</td>
                <td>{data.get('subject', '')}</td>
                <td>{data.get('labels', '')}</td>
                <td>{data.get('mail_read', '')}</td>
                <td>{data.get('mail_snippet', '')}</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.html"

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)



