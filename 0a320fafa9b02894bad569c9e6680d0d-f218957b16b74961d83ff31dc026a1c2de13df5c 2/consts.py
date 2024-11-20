from datetime import datetime

curr_date = datetime.now().strftime("%m/%d")

query_string = """project in (INIT) AND Status NOT IN (Duplicate) AND (("Eng Team[Select List (multiple choices)]" IN ("Cloud Platform - Compute", "Cloud Platform - Control Plane", "Cloud Platform - Cloud Events", "Cloud Platform - Infra Automation & Optimization", "Cloud Platform - KPT Compute & Storage Infra", "Cloud Platform - Compute") OR "Teams with Dependencies[Select List (multiple choices)]" IN ("Cloud Platform - Compute", "Cloud Platform - Control Plane", "Cloud Platform - Cloud Events", "Cloud Platform - Infra Automation & Optimization", "Cloud Platform - KPT Compute & Storage Infra", "Cloud Platform - Compute"))  AND "Current Status[Dropdown]" IN ("🔴 Red", "🟡 Yellow")) ORDER BY cf[11908] ASC, updated ASC"""

page_first_val = """<p><a href="https://confluentinc.atlassian.net/wiki/spaces/CIRE/pages/3601532117"><span style="color: rgb(7,71,166);"><u>go/cip-exec-review-notes</u></span></a></p>
<p><a href="https://confluentinc.atlassian.net/wiki/spaces/CIRE/pages/3671917908/Automation+Testing+CIP+Cloud+Platform+Execution+Review">For Other Exec Reviews</a> </p>
<p><a href="https://confluentinc.atlassian.net/wiki/spaces/CIRE/pages/3679947772/CIP+Cloud+Platform+Execution+Review+-+2024-09-24">Prev Page Link</a></p>
<p><strong><u>Agenda:</u></strong></p>
<ol start="1">
<li>
<p>Review <strong><span style="color: rgb(191,38,0);">RED</span></strong> &amp; <strong><span style="color: rgb(255,196,0);">YELLOW</span></strong> INITs which needs discussion and decision with CIP leadership for resolution or escalation (<a href="https://www.google.com/url?q=https://structure.app/structure/share/confluentinc.atlassian.net/609?v%3D18ac1c50-5f02-11ee-ba13-91a0d0fa23c0&amp;sa=D&amp;source=calendar&amp;ust=1723513108857641&amp;usg=AOvVaw0GM_DxbwRcyi9991qqcYXw"><u>go/inits</u></a>) before this issues are surfaced at weekly Exec Review meeting. (<a href="https://www.google.com/url?q=https://confluent.slack.com/archives/CBAM79KCM/p1722375557003099?thread_ts%3D1721621520.387029%26cid%3DCBAM79KCM&amp;sa=D&amp;source=calendar&amp;ust=1723513108857641&amp;usg=AOvVaw3XGVy93BYWMYzXdY9LJDS-"><u>R &amp; Y guidance</u></a>)&nbsp;</p></li>
<li>
<p>Follow-up on the AIs from previous discussion and key topics for deep dive discussion with Eng &amp; Product leads.&nbsp;</p></li>
<li>
<p>TPMs will be team level internal reviews and help finalizing the items that needs reviews from CIP Leads and post the latest updates here by Mon noon PT every week.</p></li></ol>
<p><strong><u>Reviewers</u></strong>: CIP Eng and PM leads</p>"""

table_header_val = """<p />
<table data-table-width="760" data-layout="default" ac:local-id="0318fde6-7251-4ff3-bc7a-77aad134e0e4" data-table-display-mode="default"><colgroup><col style="width: 95.0px;" /><col style="width: 664.0px;" /></colgroup>
<tbody>
<tr>
<th>
<p><strong>Date</strong></p></th>
<th>
<p><strong>Topics for discussion</strong></p></th></tr>"""

table_first_col_val = """<tr><td><p>""" + curr_date + """</p></td>"""
table_second_col_const = """<td><p><strong>Cloud Platform &mdash; Control Plane/ Compute / IAO (TPMs: </strong><ac:link><ri:user ri:account-id="60744e43852e71006c5678b2" ri:local-id="70df8fe8-c6b5-4e2b-9adb-b7f7f072f9c0" /></ac:link> <ac:link><ri:user ri:account-id="712020:57c87adb-4a35-43b2-961a-5121dec7a24e" ri:local-id="35ab3d94-3f41-4f59-b1a8-cb34054c81b7" /></ac:link> <ac:link><ri:user ri:account-id="712020:19c8f7cd-3493-4096-ba83-31101eaa8225" ri:local-id="04985f28-7c40-465f-8bc4-26a2081f96df" /></ac:link>   )</p><p>See <a href="https://confluentinc.atlassian.net/issues/?filter=31272">Jira Reference</a> </p>"""

table_footer_val = """<td><p /></td></tr></tbody></table><p />"""

# Change History Table
change_history_table_header = """<p />
<table data-table-width="1246" data-layout="default" ac:local-id="7663ac8f-6d7d-4aa9-bbb4-24aca1d4f5c3">
<tbody>
<tr>
<th>
<p><strong>Key</strong></p></th>
<th>
<p><strong>Summary</strong></p></th>
<th>
<p><strong>Current Status</strong></p></th>
<th>
<p><strong>Current Status Change History</strong></p></th></tr>"""


change_history_table_footer = """<tr>
<td>
<p /></td>
<td>
<p /></td>
<td>
<p /></td>
<td>
<p /></td></tr></tbody></table>
<p />
<p />
<p />"""
