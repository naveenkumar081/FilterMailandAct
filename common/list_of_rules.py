class Rules:
    rules_list = [
        {
            "type": "any",
            "conditions": [
                {
                    "field_name": "subject",
                    "predicate": "contains",
                    "value": "Cloud "
                },
                {
                    "field_name": "From",
                    "predicate": "equal",
                    "value": "noreply@redditmail.com"
                },
                {
                    "field_name": "sent_time",
                    "predicate": "Greater Than",
                    "value": "1 Days"
                },
            ],
            "actions": [
                {
                    "action_name": "mark message",
                    "value": "Read"
                }
            ]
        },
        {
            "type": "all",
            "conditions": [
                {
                    "field_name": "subject",
                    "predicate": "equals to",
                    "value": "Business"
                },
                {
                    "field_name": "From",
                    "predicate": "contains",
                    "value": "google.com"
                },
                {
                    "field_name": "sent_time",
                    "predicate": "Greater Than",
                    "value": "120 Hours"
                }
            ],
            "actions": [
                {
                    "action_name": "mark message",
                    "value": "Read"
                }
            ]
        }
    ]