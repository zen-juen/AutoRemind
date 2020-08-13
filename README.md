# Automate Reminder Emails for Research Participants
**AutoRemind** is an email automation system for sending customizable reminders to participants at different timepoints throughout a study.
This code was written for a study protocol where each participant has 2 sessions of experiments (on two separate days), and
- Has to be contacted *one day before* each session
- Has to be contacted *on the morning of* each session


Running `autoremind.py` will mass send the desired mails to your participants together with printed feedback on how many subjects were contacted:
```
runfile('C:/Users/Zen Juen/OneDrive/Documents/GitHub/AutoRemind/autoremind.py', wdir='C:/Users/Zen Juen/OneDrive/Documents/GitHub/AutoRemind')
Retrieving participants particulars

2 eligible participants contacted.
3 ineligible participants contacted.
Sending successful eligibility outcome to: ['Subject11', 'Subject12']
Sending unsuccessful eligibility outcome to: ['Subject19', 'Subject20', 'Subject21']
one day before: No session 1 participants to be contacted.
one day before: 1 participants to be contacted for session 2.
Sending reminder emails to: ['Subject_3'].
experiment day: No session 1 participants to be contacted.
experiment day: 2 participants to be contacted for session 2.
Sending health and travel declaration forms to: ['Subject_1', 'Subject_2']
```
P.S. This package was borne out of a personal exasperating experience of manually emailing participants :smile:

Still a **Work in Progress** :octocat:
Feel free to reach out if you've got any suggestions on how to improve / problems with the code!


## Other Resources
- [autoemailer.py](https://github.com/colinquirk/autoemailer/) which also greatly inspired this repository!
