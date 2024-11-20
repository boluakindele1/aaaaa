#!/usr/bin/python3
import logging
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from jira import JIRA
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

# Constants
BASE_URL = 'https://confluentinc.atlassian.net/wiki/rest/api'

HEADERS = {
	"Accept": "application/json",
	"Content-Type": "application/json",
	"Authorization": f"Basic {os.environ.get('ENCODED_PWD')}"
}

# Environment Variables
TPM_CHANNEL_ID = os.getenv("TPM_CHANNEL_ID")
TEST_CHANNEL_ID = os.getenv("TEST_CHANNEL_ID")


# Track Last Modifier of TLDR & Next Steps
def get_last_modifier_data():
	out = []
	query_string = """project in (INIT) AND Status NOT IN (Duplicate) AND (("Eng Team[Select List (multiple choices)]" IN ("Cloud Platform - Compute", "Cloud Platform - Control Plane", "Cloud Platform - Cloud Events", "Cloud Platform - Infra Automation & Optimization", "Cloud Platform - KPT Compute & Storage Infra", "Cloud Platform - Compute") OR "Teams with Dependencies[Select List (multiple choices)]" IN ("Cloud Platform - Compute", "Cloud Platform - Control Plane", "Cloud Platform - Cloud Events", "Cloud Platform - Infra Automation & Optimization", "Cloud Platform - KPT Compute & Storage Infra", "Cloud Platform - Compute"))  AND "Current Status[Dropdown]" IN ("🔴 Red", "🟡 Yellow")) ORDER BY cf[11908] ASC, updated ASC"""
	jira = JIRA('https://confluentinc.atlassian.net',
	            basic_auth=(os.getenv("ATLASSIAN_USERNAME"), os.getenv("ATLASSIAN_PASSWORD")))
	
	start_at = 0
	max_results = 100
	
	while True:
		issues_Jql = jira.search_issues(jql_str=query_string, expand='changelog', startAt=start_at,
		                                maxResults=max_results)
		if not issues_Jql:
			break
		for issue in issues_Jql:
			consolidated_info = get_consolidated_info(issue)
			simplified_info = construct_simplified_info(issue, consolidated_info)
			
			out.append(simplified_info)
		
		start_at += max_results
	
	return out


def get_consolidated_info(issue):
	changelog = issue.changelog
	latest_changes = {'TLDR': None, 'Next Steps': None}
	
	for history in changelog.histories:
		for item in history.items:
			if item.field in latest_changes:
				if latest_changes[item.field] is None or history.created > latest_changes[item.field]['created']:
					latest_changes[item.field] = {
						'issue_key': issue.key,
						'field': item.field,
						'created': history.created,
						'author_email': history.author.emailAddress
					}
	return latest_changes


def construct_simplified_info(issue, latest_changes):
	current_status_val = issue.raw['fields'].get('customfield_14218').get('value')
	issue_type = issue.fields.issuetype.name
	summary = issue.fields.summary
	tldr_val = getattr(issue.fields, 'customfield_13786', None)
	next_steps_val = getattr(issue.fields, 'customfield_11558', None)
	status_val = issue.fields.status.name
	assignee = issue.fields.assignee.emailAddress if issue.fields.assignee else None
	target_release_month_val = issue.raw['fields'].get('customfield_14353').get('value')
	initiative_type_val = issue.raw['fields'].get('customfield_12069').get('value')
	
	tldr_date, next_steps_date = parse_dates(latest_changes)
	latest_change_date, latest_author = get_latest_change_info(tldr_date, next_steps_date, latest_changes)
	
	return {
		'type': issue_type,
		'current_status': current_status_val,
		'key': issue.key,
		'summary': summary,
		'assignee': assignee,
		'updated': latest_change_date,
		'tldr': tldr_val,
		'next_steps': next_steps_val,
		'target_release_month': target_release_month_val,
		'updated_by': latest_author,
		'status': status_val,
		'initiative_type': initiative_type_val
	}


def parse_dates(latest_changes):
	tldr_date = datetime.strptime(latest_changes['TLDR']['created'], '%Y-%m-%dT%H:%M:%S.%f%z') if latest_changes[
		'TLDR'] else None
	next_steps_date = datetime.strptime(latest_changes['Next Steps']['created'], '%Y-%m-%dT%H:%M:%S.%f%z') if \
		latest_changes['Next Steps'] else None
	return tldr_date, next_steps_date


def get_latest_change_info(tldr_date, next_steps_date, latest_changes):
	if tldr_date and next_steps_date:
		if tldr_date > next_steps_date:
			return latest_changes['TLDR']['created'], latest_changes['TLDR']['author_email']
		else:
			return latest_changes['Next Steps']['created'], latest_changes['Next Steps']['author_email']
	elif tldr_date:
		return latest_changes['TLDR']['created'], latest_changes['TLDR']['author_email']
	elif next_steps_date:
		return latest_changes['Next Steps']['created'], latest_changes['Next Steps']['author_email']
	else:
		return None, None


def notify(channel_id, blocks_obj):
	client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
	logger = logging.getLogger(__name__)
	
	# ID of the channel you want to send the message to
	channel_id = channel_id
	
	try:
		# Call the chat.postMessage method using the WebClient
		result = client.chat_postMessage(
			channel=channel_id,
			blocks=blocks_obj
		)
		logger.info(result)
	
	except SlackApiError as e:
		logger.error(f"Error posting message: {e}")


if __name__ == '__main__':
	jira_issues_list = get_last_modifier_data()  # This gives list of all Jira Issues
	date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
	pst_zone = pytz.timezone('US/Pacific')
	
	curr_date = datetime.strptime(datetime.now(pytz.utc).strftime(date_format), date_format)
	if len(jira_issues_list) > 0:
		block_section = [{"type": "section", "text": {"type": "mrkdwn",
		                                              "text": "<!subteam^S07N03BFDPV> \n *Due:* _Mon EOD_\n  Fill *_TLDR_*, *_Next Steps_* for these R/Y Initiatives ahead of the _Weekly Chad/Shaun Exec Review_"}},
		                 {"type": "divider"}]
		for row in jira_issues_list:
			issue_type = row['type']
			current_status = row['current_status']
			issue_key = row['key']
			issue_url = "https://confluentinc.atlassian.net/browse/" + issue_key
			assignee = row.get('assignee')
			summary = row['summary']
			updated_str = row['updated']
			updated = datetime.strptime(updated_str, date_format)
			
			diff = curr_date - updated
			days_diff = diff.days
			
			updated_by = row['updated_by']
			tldr = row['tldr']
			next_steps = row['next_steps']
			
			# Get issue custom fields data and create a table
			# Call the update page function
			if days_diff > 5:
				pst_time = updated.astimezone(pst_zone)
				pst_time_str = pst_time.strftime('%Y-%m-%d %H:%M:%S')
				
				issue_block = {
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"*<{issue_url}|{issue_key}>*\n\n *Type*: _{issue_type}_ \n\n *Current Status*: _{current_status}_ \n\n  *Summary*: _{summary}_ \n\n *Last Updated*: _{pst_time_str}_"
					}
				}
				block_section.append(issue_block)
		print(len(block_section))
		
		# Send Slack Notification
		if len(block_section) > 1:
			# notify(channel_id=TEST_CHANNEL_ID, blocks_obj=block_section)
			notify(channel_id=TPM_CHANNEL_ID, blocks_obj=block_section)
		else:
			print("No Filtered Jira Issues found")
			print("Skipping Slack Notification")
	else:
		print("No Jira Issues found")
		print("Skipping Slack Notification")
