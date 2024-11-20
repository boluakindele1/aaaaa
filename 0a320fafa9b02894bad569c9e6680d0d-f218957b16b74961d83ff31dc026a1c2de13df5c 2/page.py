import os
import difflib
import re
import pytz
import app
import consts
from datetime import datetime, timedelta
from atlassian import Confluence
from jira import JIRA
import markdown
from dotenv import load_dotenv

load_dotenv()

# Constants
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")
HEADERS = {
	"Accept": "application/json",
	"Content-Type": "application/json",
	"Authorization": f"Basic {os.environ.get('ENCODED_PWD')}"
}

confluence = Confluence(
	url='https://confluentinc.atlassian.net',
	username=os.environ.get("ATLASSIAN_USERNAME"),
	password=os.environ.get("ATLASSIAN_PASSWORD"),
	cloud=True
)

jira = JIRA('https://confluentinc.atlassian.net',
            basic_auth=(os.getenv("ATLASSIAN_USERNAME"), os.getenv("ATLASSIAN_PASSWORD")))


def calculate_next_tuesday(current_date):
	"""
	:param current_date: The current date from which the next Tuesday is to be calculated. This should be a datetime.date object.
	:return: A datetime.date object representing the next Tuesday from the given current_date.
	"""
	days_ahead = (1 - current_date.weekday() + 7) % 7 or 7
	return current_date + timedelta(days=days_ahead)


def create_or_update_page(page_title, body_storage):
	"""
	:param page_title: The title of the Confluence page to be created or updated.
	:type page_title: str
	:param body_storage: The storage format body content for the Confluence page.
	:type body_storage: str
	:return: None
	:rtype: None
	"""
	try:
		res = confluence.update_or_create(PARENT_PAGE_ID, page_title, body_storage, representation='storage',
		                                  full_width=True)
		print(res)
	except Exception as e:
		print(e)


# Get Changes to a field in the last 4 weeks
def get_last_4_field_changes(issue, field_name):
	"""
	:param issue: The issue object containing the changelog and other relevant information.
	:param field_name: The name of the field for which to retrieve the last 4 changes.
	:return: A list of dictionaries containing the date, value, and key of the last 4 changes for the specified field, sorted by date in descending order.
	"""
	changelog = issue.changelog
	changes = []
	pst = pytz.timezone('America/Los_Angeles')
	for history in changelog.histories:
		history_created = datetime.strptime(history.created, '%Y-%m-%dT%H:%M:%S.%f%z')
		history_created_pst = history_created.astimezone(pst).strftime('%Y-%m-%d %H:%M:%S')
		for item in history.items:
			if item.field == field_name and item.toString:
				changes.append((history_created_pst, item.toString, issue.key))
	
	# Sort changes by date in descending order and return the last 4 changes
	changes.sort(key=lambda x: x[0], reverse=True)
	# Convert to a list of dictionaries
	changes = [{'date': change[0], 'value': change[1], 'key': change[2]} for change in changes]
	return changes[:4]


def get_latest_field_change(issue, field_name):
	"""
	:param issue: The issue object which contains the changelog information.
	:param field_name: The name of the field for which the latest change is to be retrieved.
	:return: A dictionary containing details of the latest change for the specified field, including the issue key, field name, creation timestamp, author's email address, and the from/to values. Returns None if there are no changes for the specified field.
	"""
	changelog = issue.changelog
	latest_change = None
	for history in changelog.histories:
		for item in history.items:
			if item.field == field_name:
				if latest_change is None or history.created > latest_change['created']:
					latest_change = {
						'issue_key': issue.key,
						'field': item.field,
						'created': history.created,
						'author_email': history.author.emailAddress,
						'from': item.fromString,
						'to': item.toString
					}
	return latest_change


def get_added_markdown_text(issue, field_name):
	"""
	:param issue: The issue object containing field changes.
	:param field_name: The name of the field to check for its latest change.
	:return: Added lines in markdown text format.
	"""
	latest_change = get_latest_field_change(issue, field_name)
	if latest_change:
		diff_generator = difflib.ndiff((latest_change['from'] or "").splitlines(),
		                               (latest_change['to'] or "").splitlines())
		added_lines = [line[2:] for line in diff_generator if line.startswith('+ ')]
		return '\n'.join(added_lines)
	return ""


def convert_markdown_text(markdown_text):
	"""
	:param markdown_text: The markdown text string that needs to be converted.
	:return: The converted markdown text with specific transformations applied:
	    - Replace occurrences of '# ' with incremented numbers.
	    - Convert text enclosed with '+' to underlined text.
	    - Convert JIRA-like ticket references to hyperlinks.
	    - Convert text in the form of [text|url] to standard markdown hyperlinks.
	"""
	markdown_text = re.sub(r'# ', lambda m, start=[0]: '{}/ '.format(start[0] + 1 if (start := [1])[0] else ""),
	                       markdown_text.strip(), flags=re.M)
	markdown_text = re.sub(r'\+([^\+]+)\+', r'<u>\1</u>', markdown_text)
	markdown_text = re.sub(
		r'\b([A-Z]+-\d+)\b',
		r'[\1](https://confluentinc.atlassian.net/browse/\1)',
		markdown_text
	)
	markdown_text = re.sub(r'\[([^\|\]]+)\|\s*(http[^\]]+)\]', r'[\1](\2)', markdown_text)
	return markdown.markdown(markdown_text, extensions=['extra', 'sane_lists'])


def process_issue(issue):
	"""
	:param issue: A dictionary containing details of a JIRA issue, including 'initiative_type', 'key', 'current_status', and 'summary'.
	:return: A formatted string containing the issue's initiative type, current status, summary, JIRA link, TLDR, and next steps.
	"""
	initiative_type = {
		"Eng Local": "LOCAL",
		"Product": "PRODUCT",
		"Eng Horizontal": "HORIZONTAL"
	}.get(issue['initiative_type'], "UNKNOWN")
	
	issue_obj = jira.issue(issue['key'], expand='changelog,renderedFields')
	tldr_filtered = convert_markdown_text(get_added_markdown_text(issue_obj, 'TLDR'))
	next_steps_filtered = convert_markdown_text(get_added_markdown_text(issue_obj, 'Next Steps'))
	
	return f"""
	    <p>{issue['current_status']} {issue['summary']} | <a href="https://confluentinc.atlassian.net/browse/{issue['key']}">{issue['key']}</a></p><br />
	    <p><strong>TLDR</strong>: {tldr_filtered}</p><br />
	    <p><strong>Next Steps</strong>: {next_steps_filtered}</p><br />"""


def jira_issues_search(query_string):
	"""
	Searches for Jira issues using a specified JQL query, retrieves their changelogs, and extracts
	the last four changes to the 'Current Status' field along with the summary and the current status of each issue.

	:return: A list of dictionaries containing the last four field changes to the 'Current Status' of each issue,
	         along with the summary and the current status.
	"""
	out = []
	start_at = 0
	max_results = 100
	
	while True:
		issues_Jql = jira.search_issues(jql_str=query_string, expand='changelog', startAt=start_at,
		                                maxResults=max_results)
		if not issues_Jql:
			break
		for issue in issues_Jql:
			summary = issue.fields.summary
			current_status = issue.fields.customfield_14218.value
			
			field_change_curr_status = get_last_4_field_changes(issue, 'Current Status')
			
			# Append jira summary to the dictionary
			for change in field_change_curr_status:
				change['summary'] = summary
				change['current_status'] = current_status
			
			# List of Changes per issue
			out.append(field_change_curr_status)
		
		start_at += max_results
	
	return out


def main():
	"""
	Main function that generates a page title, processes recent issues, gathers Jira issue statuses,
	and constructs an HTML report with change history.
	:return: None
	"""
	current_date = datetime.now()
	next_tuesday = calculate_next_tuesday(current_date).strftime('%Y-%m-%d')
	page_title = f"CIP Cloud Platform Execution Review - {next_tuesday}"
	issues_list_red_yellow = app.get_last_modifier_data()
	
	# Group issues by initiative type
	grouped_issues = {
		"Eng Local": [],
		"Eng Horizontal": [],
		"Product": []
	}
	for issue in issues_list_red_yellow:
		initiative_type = issue.get('initiative_type')
		if initiative_type in grouped_issues:
			grouped_issues[initiative_type].append(issue)
	
	body_val = consts.page_first_val + consts.table_header_val + consts.table_first_col_val + consts.table_second_col_const
	
	# Preserve order based on initiative type
	order = ["Eng Local", "Eng Horizontal", "Product"]
	for category in order:
		if grouped_issues[category]:
			if category == "Eng Local":
				heading = "+++LOCAL+++"
			elif category == "Eng Horizontal":
				heading = "+++HORIZONTAL+++"
			elif category == "Product":
				heading = "+++PRODUCT+++"
			else:
				heading = "+++{category}+++"
			# Add the heading once for each initiative type
			body_val += f"<p><strong>{heading}</strong></p><br/>"
			for issue in grouped_issues[category]:
				body_val += process_issue(issue)
	
	body_val += f"</td></tr>{consts.table_footer_val}"
	body_val += consts.change_history_table_header
	
	# Get the list of issues that are in the 'Red/Yellow' status
	query_string = """filter=31272"""
	issues_list_ryg = jira_issues_search(query_string)
	
	# Create a table with the following columns: Key, Summary, Current Status Value
	for issue_field_obj in issues_list_ryg:
		if issue_field_obj:
			issue_key = issue_field_obj[0]['key']
			issue_summary = issue_field_obj[0]['summary']
			issue_current_status = issue_field_obj[0]['current_status']
			curr_status_val_list = []
			for change_obj in issue_field_obj:
				# Add date and val in one string
				curr_status_time_raw = change_obj.get('date', 'No Date')
				curr_status_val = change_obj.get('value', 'No Value')
				# Extract the date part from datetime string
				try:
					curr_status_time = datetime.strptime(curr_status_time_raw, '%Y-%m-%d %H:%M:%S').date().strftime(
						'%m/%d/%Y')
				except ValueError:
					curr_status_time = 'Invalid Date'
				curr_status_val = "<em>" + curr_status_time + "</em>" + " - " + curr_status_val
				curr_status_val_list.append(curr_status_val)
			curr_status_val_bullets = ''.join([f"• {val}<br>" for val in curr_status_val_list])
			body_val += f"<tr><td><p><a href=\"https://confluentinc.atlassian.net/browse/{issue_key}\">{issue_key}</p></td><td><p><strong>{issue_summary}</strong></p></td><td><p>{issue_current_status}</p></td><td><p>{curr_status_val_bullets}</p></td></tr>"
	body_val += consts.change_history_table_footer
	
	create_or_update_page(page_title, body_val)


if __name__ == '__main__':
	main()

