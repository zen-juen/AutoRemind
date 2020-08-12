# Automate Reminder Emails for Research Participants
**AutoRemind** is an email automation system for sending customizable reminders to participants at different timepoints throughout a study.
This code was written for a study protocol where each participant has 2 sessions of experiments (on two separate days), and
- Has to be contacted *one day before* each session
- Has to be contacted *on the morning of* each session


Running `autoremind.py` will mass send the desired mails to your participants together with printed feedback on how many subjects were contacted:
```
one day before: No session 1 participants to be contacted.
one day before: No session 2 participants to be contacted.
experiment day: 3 participants to be contacted for session 1.
experiment day: No session 2 participants to be contacted.
```
P.S. This package was borne out of a personal exasperating experience of manually emailing participants :smile:

Still a **Work in Progress** :octocat:
Feel free to reach out if you've got any suggestions on how to improve / problems with the code!


## Other Resources
- [autoemailer.py](https://github.com/colinquirk/autoemailer/) which also greatly inspired this repository!
