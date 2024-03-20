import discord
import json
import random

'''
[WARNING] - REQUIRES LOCAL FILE IN PATH "reports_log.json"
'''

def get_data(key):
    try:
        with open("reports_log.json") as f:
            return json.load(f).get(key, 0)
    except FileNotFoundError:
        # If the file doesn't exist, return a default value
        return 0

def exists(user):
    with open("reports_log.json") as f:
        return str(user) in f

class Report:
    # Member member.user        -> Member object            (required)
    # string message.content?   -> Content being reported   (optional) : None
    # int severity?             -> Severity of infraction   (optional) : 1
    # string reason?            -> Report reason            (optional) : None
    # bool manual?              -> Automatic report?        (optional) : False
    def __init__(self, user: discord.Member, content=None, severity=1, reason=None, manual=False):
        self.user = user
        self.case_id = random.getrandbits(32)
        self.content = content
        self.severity = severity
        self.reason = reason
        self.manual = manual
    
    def __str__(self):
        return f"User: {self.user}, Case ID: {self.case_id}, Content: {self.content}, Sev: {self.severity}, Reason: {self.reason}"
    
    def case_data(self):
        if self.reason in [None, '', ' ']:
            self.reason = "None"
        if self.content in [None, '', ' ']:
            self.content = "None"
        return {
            "case_id": self.case_id,
            "content": self.content,
            "severity": self.severity,
            "reason": self.reason,
            "manual": self.manual
        }

    def log(self):
        # Load existing data if it exists
        try:
            with open("reports_log.json", 'r') as f:
                existing_data = json.load(f)
        except FileNotFoundError:
            existing_data = {}
        
        # Check if the user already has data in the JSON
        user_data = existing_data.get(str(self.user), {})
        if user_data == {}:
            # If the user's data doesn't exist, create a new entry
            user_data = {
                "warnings_today": 0,
                "total_warning_count": 0,
                "warnings": []
            }
        
        # Append the new report to the user's warnings list
        user_data["warnings"].append(self.case_data())
        user_data["warnings_today"] += 1
        user_data["total_warning_count"] += 1

        # Update or add the user's data in the existing data
        existing_data[str(self.user)] = user_data

        # Write the updated data back to the file
        with open("reports_log.json", 'w') as f:
            json.dump(existing_data, f, indent=4)
