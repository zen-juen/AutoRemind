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

def get_participants(get_eligible=True, get_ineligible=True, get_scheduled=True, path=None):

    # Eligible participants
    if get_eligible:
        participants_good = pd.read_csv('example_eligible.csv')

#        Set path if there are multiple files
#        path = r'C:\Users\Zen Juen\Dropbox\Deception_MockCrime\Deception_MockCrime\Participants'

#        participants_good_files = [f for f in glob.glob(os.path.join(path, "*.csv")) if f.__contains__('Passed')]
#        participants_good_csv = (pd.read_csv(f) for f in participants_good_files)
#        participants_good = pd.concat(participants_good_csv, ignore_index=True)

    # Ineligible participants
    if get_ineligible:
        participants_bad = pd.read_csv('example_ineligible.csv')

#        participants_bad_files = [f for f in glob.glob(os.path.join(path, "*.csv")) if f.__contains__('Failed')]
#        participants_bad_csv = (pd.read_csv(f) for f in participants_bad_files)
#        participants_bad = pd.concat(participants_bad_csv, ignore_index=True)

    # Scheduled participants
    if get_scheduled:
        participants_confirmed = pd.read_csv('example_scheduled.csv')
#    participants_confirmed.columns = participants_confirmed.iloc[0]
#    participants_confirmed = participants_confirmed.reindex(participants_confirmed.index.drop(0)).reset_index(drop=True)

    participants_list = [participants_good, participants_bad, participants_confirmed]

    return participants_list


# =============================================================================
# Target participants
# =============================================================================


def target_participants(participants_list, send_when="one day before", silent=False):
    """
    Target scheduled participants to be contacted either "one day before" or "experiment day"

    Parameters
    ----------
    participants_list: pd.DataFrame
        This code has the column names ['Participant Name', 'Subject ID',
        'Email', 'Phone', 'Date_Session1', 'Location_Session1', 'Timeslot_Session1',
        'Date_Session2', 'Location_Session2', 'Timeslot_Session2']
    send_when: str
        Can be 'one day before' or on 'experiment day'
    silent: bool
        Prints number of participants to be contacted.

    """
    participants_confirmed = participants_list[2]

    if send_when == "one day before":
        target_date = datetime.date.today() + datetime.timedelta(days=1)
    elif send_when == "experiment day":
        target_date = datetime.date.today()

    send_session1 = []
    send_session2 = []

    for index, row in participants_confirmed.iterrows():
        # if row['Date_Session1'] is an object as is formatted by some excel, then use
        # 'row['Date_Session1'].date() == target_date
        if datetime.datetime.strptime(row['Date_Session1'], '%d/%m/%Y').date() == target_date:
            send_session1.append(row)
        elif datetime.datetime.strptime(row['Date_Session2'], '%d/%m/%Y').date() == target_date:
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


def target_eligibility(participants_list, silent=False,
                       last_passed='Subject3', last_failed='Subject5'):
    """Target participants based on eligibility
    Input arguments `last_passed` and `last_failed` to exclude prior
    participants who have already been informed about their eligibility.
    """

    participants_good = participants_list[0]
    participants_bad = participants_list[1]

    # Eligible
    idx_p = np.where(participants_good['Name'] == last_passed)[0]
    send_eligible = participants_good.iloc[int(idx_p)+1:len(participants_good)]
    if silent is False:
        print(f'{len(send_eligible)}' + " eligible participants contacted.")

    # Ineligible
    idx_f = np.where(participants_bad['Name'] == last_failed)[0]
    send_ineligible = participants_bad.iloc[int(idx_f)+1:len(participants_bad)]
    if silent is False:
        print(f'{len(send_ineligible)}' + " ineligible participants contacted.")

    return send_eligible, send_ineligible

# =============================================================================
# Inform Eligibility Emails
# =============================================================================

def send_inform_eligible(participants_list, message_type='pass'):
    """Send eligibility outcome (message_type='pass' or 'fail') to participants"""

    retry_list = []

    # Retrieve participants
    if message_type == 'pass':
        participants = target_eligibility(participants_list, silent=True)[0]
    elif message_type == 'fail':
        participants = target_eligibility(participants_list, silent=True)[1]

    # prepare server
    from_email = secret.gmail_name
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Prepare email structure and content for sending
    for index, participant in participants.iterrows():
        to_email = participant['Email']  # activate when ready
#        to_email = 'lauzenjuen@gmail.com'

        message = MIMEMultipart('alternative')
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f'[ELIGIBILITY] Participation in "Studying the Mental Processes in Decision Making"'

        # Formatted text to be insertted
        name = f'{participant["Name"]}'

        # Main body of text
        if message_type == 'pass':
            body = """\
                Dear """ + name + """,<br><br>
                Thank you for <strong>completing the screening questionnaire</strong> for the study titled 'Studying the Mental Processes in Decision Making' (IRB NUMBER).<br><br>
                We are glad to inform you that you are <strong><u>eligible</u></strong> to participate in this study!<br><br>
                We are in the process of confirming the session slots for this study. Once new session slots are available, we will inform you as soon as possible. We appreciate your patience!<br><br>
                Please feel free to contact us at insertemailhere@gmail.com should you have any queries.<br><br>
                Thank you!<br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab
                """
        elif message_type == 'fail':
            body = """\
                Dear """ + name + """,<br><br>
                Thank you for <strong>completing the screening questionnaire</strong> for the study titled 'Studying the Mental Processes in Decision Making' (IRB NUMBER).<br><br>
                Unfortunately, you are <strong><u>not eligible</u></strong> for this study as you do not meet the study criteria. Once again, we thank you for your interest!<br><br>
                Please feel free to contact us at insertemailhere@gmail.com should you have any queries.<br><br>
                Thank you!<br><br>
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

        message = MIMEMultipart('alternative')
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f'[{message_type}'.upper() + ' REMINDER] Participation in "Studying the Mental Processes in Decision Making"'

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
        to_email = participant['Email']  # activate when ready

        message = MIMEMultipart('alternative')
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f'[{message_type}'.upper() + ' REMINDER] Health Delcaration Form for Completion"'

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

def autoremind(participants_list, silent=False,
               send_eligible=False, send_reminders=False, send_forms=False):
    """Autoremind wrapper

    Choose the type of emails to send or send all types by setting `send_eligible`, `send_reminders`,
    `send_forms` to True.
    """
    retry_total = []

    # Send eligibility
    if send_eligible:
        n_pass, n_fail = target_eligibility(participants_list, silent=silent)
        if len(n_pass) != 0:
            retry_list = send_inform_eligible(participants_list, message_type='pass')
            retry_total.append(retry_list)
            print('Sending successful eligibility outcome to: ' +
                  f'{list(n_pass["Name"])}')
        if len(n_fail) != 0:
            retry_list = send_inform_eligible(participants_list, message_type='fail')
            print('Sending unsuccessful eligibility outcome to: ' +
                  f'{list(n_fail["Name"])}')
            retry_total.append(retry_list)

    # Send one-day-prior reminders
    if send_reminders:
        daybefore_session1, daybefore_session2 = target_participants(participants_list, send_when="one day before", silent=silent)
        if len(daybefore_session1) != 0:
            retry_list = send_session_reminder(participants_list, message_type='Session 1')
            print('Sending reminder emails to: ' +
                  f'{list(np.array(daybefore_session1["Participant Name"]))}')
            retry_total.append(retry_list)
        if len(daybefore_session2) != 0:
            retry_list = send_session_reminder(participants_list, message_type='Session 2')
            print('Sending reminder emails to: ' +
                  f'{list(np.array(daybefore_session2["Participant Name"]))}')
            retry_total.append(retry_list)

    # Send health declaration forms on morning of experiment day
    if send_forms:
        actual_session1, actual_session2 = target_participants(participants_list, send_when="experiment day", silent=silent)
        if len(actual_session1) != 0:
            retry_list = send_declaration_form(participants_list, message_type='Session 1')
            print('Sending health and travel declaration forms to: ' +
                  f'{list(np.array(actual_session1["Participant Name"]))}')
            retry_total.append(retry_list)
        if len(actual_session2) != 0:
            retry_list = send_declaration_form(participants_list, message_type='Session 2')
            print('Sending health and travel declaration forms to: ' +
                  f'{list(np.array(actual_session2["Participant Name"]))}')
            retry_total.append(retry_list)

    return retry_total

# =============================================================================
# Execute
# =============================================================================


def main():
    participants_list = get_participants()
    print('Retrieving participants particulars')

    # Run this only when ready!
    retry_total = autoremind(participants_list, silent=False,
                             send_eligible=True, send_reminders=True, send_forms=True)
    if len(retry_total) != 0:
        print('Some subjects could not be reached. Try manually sending.')

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_error(e)
        print('There has been an error while emailing the participants.\n\n')
        raise
    else:
        send_success()
