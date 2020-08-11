# -*- coding: utf-8 -*-
# Dependencies
import datetime
import time
import smtplib
import os
import pandas as pd
import secret

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText




def get_participants():

    # Eligible participants
    path = r'C:\Users\Zen Juen\Dropbox\Deception_MockCrime\Deception_MockCrime\Participants'

    participants_good_files = [f for f in glob.glob(os.path.join(path, "*.csv")) if f.__contains__('Passed')]
    participants_good_csv = (pd.read_csv(f) for f in participants_good_files)
    participants_good = pd.concat(participants_good_csv, ignore_index=True)

    # Ineligible participants
    participants_bad_files = [f for f in glob.glob(os.path.join(path, "*.csv")) if f.__contains__('Failed')]
    participants_bad_csv = (pd.read_csv(f) for f in participants_bad_files)
    participants_bad = pd.concat(participants_bad_csv, ignore_index=True)

    # Scheduled participants
    participants_confirmed = pd.read_excel('../For fMRI Study 2_Scheduling/Master_Participant_List.xlsx')
    participants_confirmed.columns = participants_confirmed.iloc[0]
    participants_confirmed = participants_confirmed.reindex(participants_confirmed.index.drop(0)).reset_index(drop=True)

    participants_list = [participants_good, participants_bad, participants_confirmed]

    return participants_list
#

def send_declaration_form(participants_list):

    # Filter based on session 1 or 2
    participants_confirmed = participants_list[2]
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    send_session1 = []
    send_session2 = []
    for index, row in participants_confirmed.iterrows():
        if row['Date_Session1'].date() == pd.to_datetime(today_date).date():
            send_session1.append(row)
        elif row['Date_Session2'].date() == pd.to_datetime(today_date).date():
            send_session2.append(row)
    send_session1 = pd.concat(send_session1, axis=1).T
    send_session2 = pd.concat(send_session2, axis=1).T

    from_email = secret.gmail_address
    to_email = secret.gmail_address

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

#    today = datetime.datetime.now().strftime('%x')

    for index, participant in send_session1.iterrows():
        to_email = participant['Email']

        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f'[SESSION 1 REMINDER] Health Declaration Form for Completion'
#    f'The Reminder Email System has finished executing successfully ({today}).'
        qualtrics_link = 'https://ntuhss.az1.qualtrics.com/jfe/form/SV_9KuYYtnwXhFd1lj'

        body = (
            'Hi {send_session1["Participant Name"]}, \n'
            'Before you come to NTU for Session 1 of "Studying the Mental Processes in '
            'Decision Making", please kindly complete this health and travel declaration '
            'form https://ntuhss.az1.qualtrics.com/jfe/form/SV_9KuYYtnwXhFd1lj.\n'

            'All participants will have to complete this form and be checked that they do '
            'not hit any risk factors before they are allowed to participate in our study. '
            'Thank you for your understanding! \n'
            ' \n'
            'Regards, \n'
            'Research Team \n'
            'Clinical Brain Lab'
        )

        message.attach(MIMEText(body))
        email_text = message.as_string()

    for index, participant in send_session2.iterrows():
        to_email = participant['Email']

        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f'[SESSION 2 REMINDER] Health Declaration Form for Completion'
#    f'The Reminder Email System has finished executing successfully ({today}).'

        body = (
            'Hi {send_session2["Participant Name"]}, \n'
            'Before you come to NTU for Session 1 of "Studying the Mental Processes in '
            'Decision Making", please kindly complete this health and travel declaration '
            'form http://ntuhss.az1.qualtrics.com/jfe/form/SV_2mdgszCCaZQixZr.\n'

            'All participants will have to complete this form and be checked that they do '
            'not hit any risk factors before they are allowed to participate in our study. '
            'Thank you for your understanding! \n'
            ' \n'
            'Regards, \n'
            'Research Team \n'
            'Clinical Brain Lab'
        )


    server.sendmail(from_email, to_email, email_text)


