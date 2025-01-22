#--------------------------------------------------------------------------
# MIT License
#
# Copyright (c) 2025 Qubrick
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#--------------------------------------------------------------------------

import requests
import math
import json
import re
from datetime import datetime, timedelta

#--------------------------------------------------------------------------
# Waiting Report Generator 1.2.0
#--------------------------------------------------------------------------
#
# This is a script to generate a progress report for Waiting Boy
#
# Start Date 2021-10-5 but estimate 1 day
# My Waiting History: 4.3 for 259 days (              dev    21 days, beta 162 days, rc  55 days, stable 21 days
#                     4.2 for 147 days (              dev    13 days, beta  85 days, rc  36 days, stable 13 days)
#                     4.1 for 128 days (              dev    52 days, beta  48 days, rc  19 days, stable  9 days)
#                     4.0 for 512 days (dev 112 days, alpha 112 days, beta 234 days, rc 145 days, stable 21 days)
# Note: 4.0 dev snapshot count is not completed because I'm late. 
#
#--------------------------------------------------------------------------

username = 'USERNAME'
token = 'TOKEN'

proposals_repo = 'godotengine/godot-proposals'
issues_repo = 'godotengine/godot'

count_day = (datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - datetime(2024, 8, 16)).days

header = '**Day ' + str(count_day - 11 - 142)  + '** :gdcute: \n'
header += '(' + str(count_day) + ' days from the beginning of 4.4)\n' 
header += 'Waiting for **Godot 4.4 RC**\n'
header += '\n__**What update on 4.x today ?**__\n'

footer = '\nFor daily merged pull requests, visit [Github Pulse](<https://github.com/godotengine/godot/pulse/daily>).\n'
# footer += 'For release blockers, visit [4.x Release Blockers](<https://github.com/orgs/godotengine/projects/61>).\n'
footer += 'My Waiting History: 4.4 (beta 142 days, dev 11 days), 4.3 (259 days), 4.2 (147 days), 4.1 (128 days), 4.0 (512 days)\n\nSincerely, ' + username + '.'

MAX_ISSUES = 100
MAX_PAGES = 2

# Load recorded date
f = open('rec.json') 
date_records = json.load(f)
last_datetime = datetime.strptime(date_records[-1], '%Y-%m-%dT%H:%M:%SZ')
f.close()

#--------------------------------------------------------------------------
# Get Issues Report
#--------------------------------------------------------------------------

def get_issues_report(milestone : str, repo : str, type :str, title : str, timefilter : str, state : str, state_reason = None, event = None):
    count_issues = 0
    output = ""

    label_list = { "core": "", "documentation":"", "editor":"", "gui":"", "input":"", "audio":"", 
                "rendering":"", "shaders":"", "3d":"", "2d":"", "particles":"", "vfx":"", "animation":"",  
                "physics":"", "codestyle":"", "gdscript":"", "dotnet":"", "visualscript":"",  "navigation":"", "multiplayer":"", "network":"", "xr":"", 
                "plugin":"", "gdextension":"",
                "buildsystem":"", "export": "", "import":"", "porting":"", "tests":"", "thirdparty":"" } # Label List
        
    for i in range(1, MAX_PAGES + 1):
        req = requests.get('https://api.github.com/search/issues?q=repo:' + repo + '%20is:' + type + '%20' + milestone + '%20state:' + state + '%20' + timefilter + ':>=' + last_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') + '&per_page=' + str(MAX_ISSUES) + '&page=' + str(i) + '&sort=updated', auth=(username,token))
        content = req.content.decode("utf-8")
        jsonObject = json.loads(content)

        if "total_count" in jsonObject and jsonObject["total_count"] > 0:
            for s in jsonObject["items"]:
                r = s["state_reason"]
                found_event = True

                # Check if event existed after lastime
                if event is not None and (state_reason is None or (state_reason is not None and (state_reason != event or (state_reason == event and s["state_reason"] == state_reason)))):
                    found_event = False
                    event_req = requests.get('https://api.github.com/repos/' + repo + '/issues/' + str(s["number"]) + '/events', auth=(username,token))
                    event_content = event_req.content.decode("utf-8")
                    event_jsonObject = json.loads(event_content)
                    for e in event_jsonObject:
                        if e["event"] == event:
                            datetime_e = datetime.strptime(e["created_at"], '%Y-%m-%dT%H:%M:%SZ')
                            diff = datetime_e - last_datetime
                            if diff.total_seconds() >= 0.0:
                                found_event = True
                                break

                if (state_reason is None or s["state_reason"] == state_reason) and found_event == True:

                    prefix = '' 
                    if "pull_request" in s and r is None:
                        if s["pull_request"]["merged_at"] is not None:
                            prefix = ':purple_circle: [M][PR]'
                        else:
                            prefix = ':red_circle: [C][PR]'
                    else:
                        if r == 'completed':
                            prefix = ':purple_circle: [C]' 
                        elif r == 'not_planned':
                            prefix = ':red_circle: [N]' 
                        elif r == 'reopened':
                            prefix = ':green_circle: [R]'
                        elif r == 'duplicate':
                            prefix = ':black_circle: [D]'

                    c = prefix + ' [#' + str(s["number"]) + '](<' + s["html_url"] + '>): ' + s["title"] + "\n"
                    approved = False
                    t = ""

                    for l in s["labels"]:                        
                        if approved == False:
                            if "topic:" in l["name"] or "documentation" in l["name"]:
                                t = l["name"].replace("topic:", "")
                                approved = True
                            else:
                                t = l["name"]

                    if t in label_list:
                        label_list[t] += c
                    else:
                        label_list[t] = c

                    count_issues += 1

    if count_issues > 0:        
        for l in label_list:
            if len(label_list[l].strip()) > 0:     
                output += "__**" 
                output += ("Dot Net" if l.lower() == "dotnet" else ("GDExtension" if l.lower() == "gdextension" else ("GDScript" if l.lower() == "gdscript" else (l.capitalize() if len(l) > 3 else l.upper()))))
                output += "**__\n" + label_list[l].strip() + "\n\n"    
        
        return '**' + title + (('s ('+ str(count_issues) +')') if count_issues > 1 else '') + ':**\n' + output + '\n\n'

    return None
    # END

#--------------------------------------------------------------------------
# Get Milestones Report
#--------------------------------------------------------------------------

def get_all_issues_report(milestone : str, repo : str, title : str, timefilter : str, state : str, state_reason = None, event = None) -> str:
    tmp = ""
    
    c = get_issues_report(milestone, repo, 'pull-request', state.capitalize() + " Pull Request", timefilter, state, state_reason, event)
    if c is not None:
        tmp += c + "~~----------------------------------------------------~~\n\n"

    c = get_issues_report(milestone, repo, 'issue', title, timefilter, state, state_reason, event)
    if c is not None:
        tmp += c
    return tmp

#--------------------------------------------------------------------------
# Get Milestones Report
#--------------------------------------------------------------------------

def get_milestones_report(repo : str, header : str, title : str, filter : str = "^4\.") -> str: # Only check 4.x
    res = requests.get('https://api.github.com/repos/' + repo + '/milestones', auth=(username,token))
    content = res.content.decode("utf-8")
    jobject = json.loads(content)

    tmp = ""
    for o in jobject:
        test = re.search(filter, o["title"])
        if test:
            datetime_o = datetime.strptime(o["updated_at"], '%Y-%m-%dT%H:%M:%SZ')
            diff = datetime_o - last_datetime

            # Just find out if curretn update is more than last time
            if diff.total_seconds() >= 0.0:      
                open_is = o["open_issues"]
                closed_is = o["closed_issues"]

                print(header + ' ' + o["title"] + ' - ' + str(open_is) + " open / " + str(closed_is) + " closed")

                if open_is == 0 and closed_is == 0:
                    complete_percent = 0
                else:
                    complete_percent = math.floor(100 - ((open_is * 100) / (open_is + closed_is)))

                content_existed = False
                t = ""

                # Reopened Proposals
                c = get_all_issues_report('milestone:' + o["title"], repo, 'Reopened ' + title, 'updated', 'open', 'reopened', 'reopened')            
                if len(c) > 0:
                    content_existed = True
                    t += c + '\n\n'

                # Closed Proposals  
                c = get_all_issues_report('milestone:' + o["title"], repo, 'Closed ' + title, 'closed', 'closed')
                if len(c) > 0:
                    content_existed = True
                    t += c + '\n\n'

                if content_existed is True:                
                    tmp += '\n~~----------------------------------------------------~~'                
                    tmp += '\n\n**' + header + ' ' + o["title"] + ':** ' + str(complete_percent) + '% complete '
                    tmp += '(' + f'{open_is:,}' +' open / ' + f'{closed_is:,}' + ' closed)\n' + t + '\n\n'
    return tmp  

#--------------------------------------------------------------------------
# Write Report
#--------------------------------------------------------------------------
# Header
text = header

# Proposals
text += get_milestones_report(proposals_repo, 'Proposals', 'Proposal')

# Issues
text += get_milestones_report(issues_repo, 'Milestones', 'Issue')

# Footer
text += footer

# Write Report
f = open("report.txt", "w", encoding="utf-8")
f.write(text)
f.close()

# Write Time Record
f = open("rec.json", "w", encoding="utf-8")

# Update date
date_records.append(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')) 
# Convert datetime to string use datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

f.write(json.dumps(date_records, indent = 2))
f.close()

# Write Usage Litmit
f = open("limit.json", "w", encoding="utf-8")
 
# Get github usage limit
res = requests.get('https://api.github.com/rate_limit', auth=(username,token))
content = res.content.decode("utf-8")
jobject = json.loads(content)

f.write(json.dumps(jobject, indent = 2))
f.close()

print("Done")
