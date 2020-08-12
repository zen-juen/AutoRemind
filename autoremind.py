# -*- coding: utf-8 -*-
import datetime
import smtplib
import os
import pandas as pd
import secret
import glob
import calendar
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# =============================================================================
# Extract emails
# =============================================================================

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
    participants_confirmed = pd.read_excel('C:/Users/Zen Juen/Dropbox/Deception_MockCrime/Deception_MockCrime/For fMRI Study 2_Scheduling/Master_Participant_List.xlsx')
    participants_confirmed.columns = participants_confirmed.iloc[0]
    participants_confirmed = participants_confirmed.reindex(participants_confirmed.index.drop(0)).reset_index(drop=True)

    participants_list = [participants_good, participants_bad, participants_confirmed]

    return participants_list


# =============================================================================
# Target participants
# =============================================================================


def target_participants(participants_list, send_when="one day before", silent=False):
    """
    Target participants to be contacted either "one day before" or "experiment day"
    """
    participants_confirmed = participants_list[2]

    if send_when == "one day before":
        target_date = datetime.date.today() + datetime.timedelta(days=1)
    elif send_when == "experiment day":
        target_date = datetime.date.today()

    send_session1 = []
    send_session2 = []
    for index, row in participants_confirmed.iterrows():
        if row['Date_Session1'].date() == target_date:
            send_session1.append(row)
        elif row['Date_Session2'].date() == target_date:
            send_session2.append(row)

    # Print participant details
    if len(send_session1) != 0:
        send_session1 = pd.concat(send_session1, axis=1).T
        if silent is False:
            print(f'{send_when}: ' + f'{len(send_session1)}' + " participants to be contacted for session 1.")
    else:
        if silent is False:
            print(f'{send_when}: ' + "No session 1 participants to be contacted.")

    if len(send_session2) != 0:
        send_session2 = pd.concat(send_session2, axis=1).T
        if silent is False:
            print(f'{send_when}: ' + f'{len(send_session2)}' + " participants to be contacted for session 2.")
    else:
        if silent is False:
            print(f'{send_when}: ' + "No session 2 participants to be contacted.")

    return send_session1, send_session2

# =============================================================================
# Types of Reminder Emails
# =============================================================================

def send_session_reminder(participants_list, message_type='Session 1'):
    """Send different session reminders one day before the respective sessions"""
    retry_list = []

    # prepare server
    from_email = secret.gmail_name
#    to_email = secret.gmail_address

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Session 1 Reminders
    if message_type == 'Session 1':
        participants = target_participants(participants_list,
                                           send_when="one day before", silent=True)[0]

    # Session 2 Reminders
    elif message_type == 'Session 2':
        participants = target_participants(participants_list,
                                           send_when="one day before", silent=True)[1]

    # Prepare email structure and content for sending
    for index, participant in participants.iterrows():
#        to_email = participant['Email']  # activate when ready!!!!!
        to_email = 'lauzenjuen@gmail.com'

        message = MIMEMultipart('alternative')
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f'[{message_type}' + ' Reminder] Participation in "Studying the Mental Processes in Decision Making"'

        # Formatted text to be insertted
        name = f'{participant["Participant Name"]}'
        phone = f'{participant["Phone"]}'

        date_1 = f'{participant["Date_Session1"].date().strftime("%d %B")}, {calendar.day_name[participant["Date_Session1"].weekday()]}'
        date_2 = f'{participant["Date_Session2"].date().strftime("%d %B")}, {calendar.day_name[participant["Date_Session2"].weekday()]}'
        time_1 = f'{participant["Timeslot_Session1"]}'
        time_2 = f'{participant["Timeslot_Session2"]}'
        location_1 = f'{participant["Location_Session1"]}'
        location_2 = f'{participant["Location_Session2"]}'

        # Main body of text
        if message_type == 'Session 1':
            body = """\
                Dear """ + name + """,<br><br>
                We are writing to remind you about your Session 1 slot on ‘Studying the Mental Processes of Decision Making’ tomorrow. We would like to confirm with you that you are coming for Session 1 tomorrow at: <br>
                <ul>
                <li><strong><u>Time:</u> """ + time_1 + """</strong><br>
                <li><strong><u>Date:</u> """ + date_1 + """</strong><br>
                <li><strong><u>Location:</u> Nanyang Technological University (NTU), School of Humanities and School of Social Sciences (48 Nanyang Avenue), """ + location_1 + """</strong><br>
                </ul><br><br>
                OTHER TEXT HERE <br>
                <br>
                Regards<br>
                Research Team<br>
                Clinical Brain Lab<br>
                """

        elif message_type == 'Session 2':
            body = """\
                Dear """ + name + """,<br><br>
                This email is to remind you about your Session 2 on ‘Studying the Mental Processes of Decision Making’ tomorrow. We will like to confirm with you that you are coming for Session 2 tomorrow at <br>
                <ul>
                <li><strong><u>Time</u>: """ + time_2 + """</strong><br>
                <li><strong><u>Date</u>: """ + date_2 + """</strong><br>
                <li><strong><u>Location</u>: Nanyang Technological University (NTU), School of Humanities and School of Social Sciences (48 Nanyang Avenue), """ + location_2 + """</strong>
                </ul><br><br>
                OTHER TEXT HERE <br>
                <br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab<br>
                """

        message.attach(MIMEText(body, 'html'))
        email_text = message.as_string()
        try:
            server.sendmail(from_email, to_email, email_text)
        except Exception as e:
            retry_list.append(participant)
            continue

    return retry_list

def send_declaration_form(participants_list, message_type='Session 1'):
    """Health and travel declaration forms to be sent on the morning of each session"""
    retry_list = []

    # prepare server
    from_email = secret.gmail_name
#    to_email = secret.gmail_address

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Session 1 Reminders
    if message_type == 'Session 1':
        participants = target_participants(participants_list,
                                           send_when="experiment day", silent=True)[0]

    # Session 2 Reminders
    elif message_type == 'Session 2':
        participants = target_participants(participants_list,
                                           send_when="experiment day", silent=True)[1]

    # Prepare email structure and content for sending
    for index, participant in participants.iterrows():
#        to_email = participant['Email']  # activate when ready
        to_email = 'lauzenjuen@gmail.com'

        message = MIMEMultipart('alternative')
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f'[{message_type}' + ' Reminder] Health Delcaration Form for Completion"'

        # Formatted text to be insertted
        name = f'{participant["Participant Name"]}'

        # Main body of text
        if message_type == 'Session 1':
            body = """\
                Dear """ + name + """,<br><br>
                Before you come to NTU for Session 1 of "Studying the Mental Processes in
                Decision Making" today, please kindly complete and submit this <strong>health and travel declaration
                form</strong> by <a href="https://ntuhss.az1.qualtrics.com/jfe/form/SV_9KuYYtnwXhFd1lj">clicking here</a>.<br><br>
                All participants will have to complete this form as part of the COVID-19 safety measures.<br><br>
                Thank you for your understanding!<br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab
                """
        elif message_type == 'Session 2':
            body = """\
                Dear """ + name + """,<br><br>
                Before you come to NTU for Session 2 of "Studying the Mental Processes in
                Decision Making" today, please kindly complete and submit this <strong>health and travel declaration
                form</strong> by <a href="http://ntuhss.az1.qualtrics.com/jfe/form/SV_2mdgszCCaZQixZr">clicking here</a>.<br><br>
                All participants will have to complete this form as part of the COVID-19 safety measures.<br><br>
                Thank you for your understanding!<br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab
                """

        message.attach(MIMEText(body, 'html'))
        email_text = message.as_string()
        try:
            server.sendmail(from_email, to_email, email_text)
        except Exception as e:
            retry_list.append(participant)
            continue

    return retry_list


# =============================================================================
# Feedback emails
# =============================================================================


def send_error(e):
    from_email = secret.gmail_name
    to_email = secret.admin_address
    cc_email = secret.gmail_address

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    today = datetime.datetime.now().strftime('%x')

    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Cc"] = cc_email
    message["Subject"] = 'ERROR: An error occured with the reminder email system ({today}).'

    body = (
        'There was an error while trying to email participants.\n\n'
        'Here is the error text:\n\n'
        f'{repr(e)}'
    )

    message.attach(MIMEText(body))
    email_text = message.as_string()

    server.sendmail(from_email, [to_email] + [cc_email], email_text)


def send_success():
    from_email = secret.gmail_name
    to_email = secret.gmail_address

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    today = datetime.datetime.now().strftime('%x')

    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = f'The Reminder Email System finished executing successfully ({today}).'

    body = (
        'No errors occured while sending emails.\n'
    )

    message.attach(MIMEText(body))
    email_text = message.as_string()

    server.sendmail(from_email, to_email, email_text)

# =============================================================================
# Wrapper for emails
# =============================================================================

def autoremind(participants_list, silent=False):
    """Autoremind wrapper"""

    # Send one-day-prior reminders
    daybefore_session1, daybefore_session2 = target_participants(participants_list, send_when="one day before", silent=silent)
    if len(daybefore_session1) != 0:
        retry_list = send_session_reminder(participants_list, message_type='Session 1')
    if len(daybefore_session2) != 0:
        retry_list = send_session_reminder(participants_list, message_type='Session 2')

    # Send health declaration forms on morning of experiment day
    actual_session1, actual_session2 = target_participants(participants_list, send_when="experiment day", silent=silent)
    if len(actual_session1) != 0:
        retry_list = send_declaration_form(participants_list, message_type='Session 1')
    if len(actual_session2) != 0:
        retry_list = send_declaration_form(participants_list, message_type='Session 2')

    return retry_list

# =============================================================================
# Execute
# =============================================================================


def main():
    participants_list = get_participants()

    retry_list = autoremind(participants_list, silent=False)

    tmp = 0

    while retry_list:
        tmp += 1
        time.sleep(3600)
        autoremind(retry_list)
        if tmp > 3:
            raise EnvironmentError('Unable to reach some participants.')
            break


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_error(e)
        print('An error occurred when emailing the participants.\n\n')
        raise
    else:
        send_success()

