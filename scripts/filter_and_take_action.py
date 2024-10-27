# This file is intended to list the mail under a mailbox and store it in the database
# !/usr/bin/env python3
import sys
import os
from datetime import datetime
from typing import Any
from typing import  Optional

from oslo_config import cfg

possible_top_dir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                 os.pardir,
                                                 os.pardir))

if os.path.exists(os.path.join(possible_top_dir, 'FilterandAct', '__init__.py')):
    sys.path.insert(0, possible_top_dir)

from common import config
from common import database_adapter
from common.definitions import TableAdapters, MailClassifications
from common import google_utils
from common.list_of_rules import Rules
from common import utils


class FilterandAct:
    def __init__(self):
        pass

    @staticmethod
    def commit_the_data_in_to_table(
            message_id: str,
            labels_in_system: list[str],
            labels_to_add: list[str],
            labels_to_remove: list[str],
            /):

        labels_to_update = ""
        mail_read = True
        distinct_labels_in_system = set(labels_in_system)
        distinct_labels_in_system.update(set(labels_to_add))
        distinct_labels_in_system.difference(set(labels_to_remove))
        final_updated_list = list(distinct_labels_in_system)
        if MailClassifications.UNREAD in final_updated_list:
            mail_read = False

        for label in final_updated_list:
            labels_to_update += f"{label},"

        set_clause = f"labels='{labels_to_update}', mail_read={mail_read}"

        where_clause = f"id='{message_id}'"

        database_adapter.instance.update_data_in_table(TableAdapters.MailDetails,
                                                       set_clause,
                                                       where=where_clause
                                                       )

    @staticmethod
    def fetch_equivalent_action_value_from_table( label_data_from_table: dict[str, Any],
                                                  action_value) -> Optional[str]:
        if not action_value:
            return None

        value_from_table = label_data_from_table.get(action_value)

        return value_from_table


    @staticmethod
    def is_action_required(
            message_details: dict[str, Any],
            action_list: list[dict[str, Any]],
            label_data_from_table: dict[str, Any],
            /
    ) -> bool:
        labels_as_strings = message_details.get("labels", "")
        label_ids = utils.convert_comma_delimited_to_list(labels_as_strings)
        for each_action in action_list:
            action_name_ = each_action.get("action_name")
            action_value = each_action.get("value")
            table_action_value = FilterandAct.fetch_equivalent_action_value_from_table(label_data_from_table, action_value)
            if action_name_.lower().startswith("move") and (action_value in label_ids or table_action_value not in label_ids):
                return True

            if action_name_.lower().startswith("mark") and action_value not in label_ids:
                return True

        return False

    @staticmethod
    def update_labels_from_actions(
            action_list: list[dict[str, Any]],
            label_data_from_tabel: dict[str,  Any],
            /,
            *,
            label_needs_to_be_update: list[str] = None,
            label_needs_to_be_removed: list[str] = None
    ) -> tuple[list[str], list[str]]:
        if not label_needs_to_be_update:
            label_needs_to_be_update = []

        if not label_needs_to_be_removed:
            label_needs_to_be_removed = []

        for each_action in action_list:
            action_name_ = each_action.get("action_name")
            action_value = each_action.get("value")

            action_value_from_table_ = FilterandAct.fetch_equivalent_action_value_from_table(label_data_from_tabel, action_value)

            if action_name_.startswith("mark"):
                if action_value == MailClassifications.UNREAD.lower():
                    label_needs_to_be_update.append(MailClassifications.UNREAD)
                else:
                    label_needs_to_be_removed.append(MailClassifications.UNREAD)
            else:
                label_needs_to_be_update.append(action_value_from_table_)

        return label_needs_to_be_update, label_needs_to_be_removed

    @staticmethod
    def filter_any_conditions(
            message_details: dict[str, Any],
            conditions: list[dict[str, Any]],
            /
    ) -> bool:
        condition_satisfied = False

        for each_condition in conditions:
            field = each_condition.get("field_name")
            predicate = each_condition.get("predicate")
            value_for_the_field_to_compare = each_condition.get("value")
            actual_value_available = message_details.get(field)
            if isinstance(actual_value_available, str):
                if utils.match_string(value_for_the_field_to_compare, actual_value_available, match_type=predicate):
                    condition_satisfied = True
                    break

            if isinstance(actual_value_available, datetime):
                if utils.update_time_values_based_on_the_result(value_for_the_field_to_compare, actual_value_available,
                                                                predicate_value=predicate):
                    condition_satisfied = True
                    break

        return condition_satisfied

    @staticmethod
    def filter_all_conditions(
            message_details: dict[str, Any],
            conditions: list[dict[str, Any]],
            /
    ) -> bool:
        condition_satisfied = True

        for each_condition in conditions:
            field = each_condition.get("field_name")
            predicate = each_condition.get("predicate")
            value_for_the_field_to_compare = each_condition.get("value")
            actual_value_available = message_details.get(field)
            if isinstance(actual_value_available, str):
                if not (
                        utils.match_string(value_for_the_field_to_compare, actual_value_available,
                                           match_type=predicate)):
                    condition_satisfied = False
                    break

            if isinstance(actual_value_available, datetime):
                if not (
                        utils.update_time_values_based_on_the_result(value_for_the_field_to_compare,
                                                                     actual_value_available,
                                                                     predicate_value=predicate)):
                    condition_satisfied = False
                    break

        return condition_satisfied

    @staticmethod
    def filter_mail_and_frame_action_dict(
            message_details: dict[str, Any],
            rules_list: list[dict[str, Any]],
            label_data_from_table: dict[str, Any],
            /
    ) -> tuple[list[str], list[str]]:
        labels_needs_to_be_updated = []
        label_needs_to_be_removed = []
        for rule_ in rules_list:
            action_needed = False
            type_of_rule = rule_.get("type", "all")
            conditions_for_rule = rule_.get("conditions", [])
            actions_for_rule = rule_.get("actions", [])
            if not conditions_for_rule:
                continue

            action_required = FilterandAct.is_action_required(message_details, actions_for_rule,
                                                                         label_data_from_table)

            if not action_required:
                continue

            if type_of_rule.lower() == "all":
                action_needed = FilterandAct.filter_all_conditions(message_details,
                                                                   conditions_for_rule)

            if type_of_rule.lower() == "any":
                action_needed = FilterandAct.filter_any_conditions(message_details,
                                                                   conditions_for_rule)

            if not action_needed:
                continue

            labels_needs_to_be_updated, label_needs_to_be_removed = (
                FilterandAct.update_labels_from_actions(actions_for_rule,
                                                        label_data_from_table,
                                                     label_needs_to_be_update=labels_needs_to_be_updated,
                                                     label_needs_to_be_removed=label_needs_to_be_removed))


        return labels_needs_to_be_updated, label_needs_to_be_removed

    @staticmethod
    def transform_label_data(label_list: list[dict[str, Any]],
                             /) -> dict[str, str]:
        final_label_data = {}
        for each_label in label_list:
            final_label_data[each_label.get("name")] = each_label.get("id")

        return final_label_data

    @staticmethod
    def filter_emails_based_on_rule():
        query_to_filter_mails = f"Select * From {TableAdapters.MailDetails}"
        query_to_filter_labels = f"Select name, id From {TableAdapters.LabelDetails} where type != 'system'"
        message_list = database_adapter.instance.execute_query(query_to_filter_mails)
        label_list = database_adapter.instance.execute_query(query_to_filter_labels)
        label_data = FilterandAct.transform_label_data(label_list)
        rules_list = Rules.rules_list
        for each_message_ in message_list:
            message_id = each_message_.get("id")
            labels = each_message_.get("labels", "")
            labels_in_list = utils.convert_comma_delimited_to_list(labels)
            label_needs_to_be_added, label_needs_to_be_removed = FilterandAct.filter_mail_and_frame_action_dict(
                each_message_, rules_list,
                label_data)
            if label_needs_to_be_added or label_needs_to_be_removed:
                google_utils.instance.update_labels_for_the_mail(message_id, labels_to_add=label_needs_to_be_added,
                                                                 labels_to_remove=label_needs_to_be_removed)
            FilterandAct.commit_the_data_in_to_table(message_id, labels_in_list, label_needs_to_be_added, label_needs_to_be_removed)

        new_message_list = database_adapter.instance.execute_query(query_to_filter_mails)
        utils.save_data_as_html_table(new_message_list)


if __name__ == '__main__':
    cfg.CONF(project='FilterandAct', version='1.0.0', prog='FilterandAct')
    print("sanity check has been initiated")
    config.startup_sanity_checks()
    print("Sanity has been completed")
    filter_obj = FilterandAct()
    print("Started Filtering mail based on the rules...")
    filter_obj.filter_emails_based_on_rule()
    print("Mail Filter has been completed. Please see the latest html file in the same directory.....")

