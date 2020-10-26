# -*- coding: utf-8 -*-
import calendar
import datetime
import glob
import imaplib
import os
import smtplib
import time
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import numpy as np
import pandas as pd

import secret

# =============================================================================
# Extract emails
# =============================================================================


def get_new():
    """Get email addresses of unread emails"""

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(secret.gmail_address, secret.gmail_password)
    mail.list()
    mail.select("inbox")
    result, data = mail.uid("search", None, "UNSEEN")  # Get all unseen
    n_unread = len(data[0].split())

    new_addresses = []
    for i in range(n_unread):
        latest_email_uid = data[0].split()[i]
        result, email_data = mail.uid("fetch", latest_email_uid, "(RFC822)")
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode("utf-8")
        email_message = email.message_from_string(raw_email_string)

        email_from = str(
            email.header.make_header(email.header.decode_header(email_message["From"]))
        )
        to = email.utils.parseaddr(email_from)[1]

        new_addresses.append(to)

    return new_addresses


def get_participants(
    get_eligible=True, get_ineligible=True, get_scheduled=True, path=None
):

    # path = r'C:\Users\Zen Juen\Dropbox\ExperimentalParadigm\Participants'

    # Eligible participants
    if get_eligible:
        if path is None:
            participants_good = pd.read_csv("example_eligible.csv")
        else:
            # Set path if there are multiple files
            participants_good_files = [
                f
                for f in glob.glob(os.path.join(path, "*.csv"))
                if f.__contains__("Passed")
            ]  # identify eligible participant folders by 'Passed' in folder name
            participants_good_csv = (pd.read_csv(f) for f in participants_good_files)
            participants_good = pd.concat(participants_good_csv, ignore_index=True)

    # Ineligible participants
    if get_ineligible:
        if path is None:
            participants_bad = pd.read_csv("example_ineligible.csv")
        else:
            participants_bad_files = [
                f
                for f in glob.glob(os.path.join(path, "*.csv"))
                if f.__contains__("Failed")
            ]  # identify ineligible participant folders by 'Failed' in folder name
            participants_bad_csv = (pd.read_csv(f) for f in participants_bad_files)
            participants_bad = pd.concat(participants_bad_csv, ignore_index=True)

    # Scheduled participants
    if get_scheduled:
        participants_confirmed = pd.read_csv("example_scheduled.csv")

    participants_list = [participants_good, participants_bad, participants_confirmed]

    return participants_list


# =============================================================================
# Identify participants for emailing
# =============================================================================


def target_eligibility(
    participants_list, silent=False, last_passed="Subject10", last_failed="Subject18"
):
    """Target participants based on eligibility.

    Input arguments `last_passed` and `last_failed` to exclude prior
    participants who have already been informed about their eligibility.
    """

    participants_good = participants_list[0]
    participants_bad = participants_list[1]

    # Eligible
    idx_p = np.where(participants_good["Name"] == last_passed)[0]
    send_eligible = participants_good.iloc[int(idx_p) + 1 : len(participants_good)]
    if silent is False:
        print(f"{len(send_eligible)}" + " eligible participants contacted.")

    # Ineligible
    idx_f = np.where(participants_bad["Name"] == last_failed)[0]
    send_ineligible = participants_bad.iloc[int(idx_f) + 1 : len(participants_bad)]
    if silent is False:
        print(f"{len(send_ineligible)}" + " ineligible participants contacted.")

    return send_eligible, send_ineligible


def target_confirmation(participants_list, silent=False):
    """
    Target participants to be contacted for confirmation of session slots
    """
    participants_confirmed = participants_list[2]
    participants = participants_confirmed[
        participants_confirmed["Timeslots Confirmed"] == "No"
    ]
    if silent is False:
        print(
            f"{len(participants)}"
            + " participants to seek confirmation of session slots."
        )

    return participants


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
        if (
            datetime.datetime.strptime(row["Date_Session1"], "%d/%m/%Y").date()
            == target_date
        ):
            send_session1.append(row)
        elif (
            datetime.datetime.strptime(row["Date_Session2"], "%d/%m/%Y").date()
            == target_date
        ):
            send_session2.append(row)

    # Print participant details
    if len(send_session1) != 0:
        send_session1 = pd.concat(send_session1, axis=1).T
        if silent is False:
            print(
                f"{send_when}: "
                + f"{len(send_session1)}"
                + " participants to be contacted for session 1."
            )
    else:
        if silent is False:
            print(f"{send_when}: " + "No session 1 participants to be contacted.")

    if len(send_session2) != 0:
        send_session2 = pd.concat(send_session2, axis=1).T
        if silent is False:
            print(
                f"{send_when}: "
                + f"{len(send_session2)}"
                + " participants to be contacted for session 2."
            )
    else:
        if silent is False:
            print(f"{send_when}: " + "No session 2 participants to be contacted.")

    return send_session1, send_session2


# =============================================================================
# Send research information to new emails
# =============================================================================
def send_researchinfo(
    new_addresses,
    link="http://ntuhss.az1.qualtrics.com/jfe/form/SV_ePZ13fZ4kPrF0wt",
    to_send=False,
    filename="poster.jpg",
    filetype="image",
):
    """
    Parameters
    ----------
    new_addresses: list
        List of email addresses.
    link: str
        Object to be included in the email body.
    to_send: bool
        If True, send the emails.
    filename: str
        The name of the file to be sent as attachment. If there is no attachment, set to None.
        The function assumes that the file is in the same location as the script.
    filetype: str
        For now, the function supports either image of pdf as attachment.

    """
    retry_list = []

    # prepare server
    from_email = secret.gmail_name
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Prepare email structure and content for sending
    for i in new_addresses:
        to_email = i  # activate when ready

        message = MIMEMultipart("alternative")
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = "[PARTICIPANTS RECRUITMENT] Experimental Paradigm"

        # Include attachment
        if filename is not None:
            if filetype == "image":
                img_data = open(filename, "rb").read()
                attachment = MIMEImage(img_data, name=os.path.basename(filename))
            elif filetype == "pdf":
                pdf_data = open(filename, "rb").read()
                attachment = MIMEApplication(
                    pdf_data, _subtype="pdf", name=os.path.basename(filename)
                )
                attachment[
                    "Content-Disposition"
                ] = 'attachment; filename="%s"' % os.path.basename(filename)
            message.attach(attachment)
        # Main body of text
        body = (
            """\
            Dear potential participant, <br><br>

            Thank you for  your interest in the study titled, 'Experimental Paradigm', as described in the poster attached in this email.<br><br>

            To determine your eligibility for this study, please complete the <strong><u>online screening questionnaire</u></strong> with the following link """
            + link
            + """. <br><br>
            We will evaluate your responses and contact you regarding your eligibility. If you have any questions, please feel free to contact us at: decisiontask.study@gmail.com.Thank you! <br><br>

            Regards,<br>
            Research Team<br>
            Clinical Brain Lab<br>
            """
        )

        message.attach(MIMEText(body, "html"))
        email_text = message.as_string()
        try:
            if to_send:
                server.sendmail(from_email, to_email, email_text)
        except Exception as e:
            retry_list.append(i)
            continue

    return retry_list


# =============================================================================
# Check confirmation of slots
# =============================================================================
def send_session_confirmation(participants_list, to_send=False):
    """Ask participants to confirm allocated slots, can be sent any day (just need
    to be sufficiently early than Session 1 and 2 dates"""
    retry_list = []

    participants = target_confirmation(participants_list, silent=True)

    # prepare server
    from_email = secret.gmail_name
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Prepare email structure and content for sending
    for index, participant in participants.iterrows():
        to_email = participant["Email"]
        #        to_email = 'lauzenjuen@gmail.com'

        message = MIMEMultipart("alternative")
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message[
            "Subject"
        ] = f'[SESSION SLOTS CONFIRMED] Participation in Experimental Paradigm"'

        # Formatted text to be insertted
        name = f'{participant["Participant Name"]}'

        date_1 = f'{participant["Date_Session1"].date().strftime("%d %B")}, {calendar.day_name[participant["Date_Session1"].weekday()]}'
        date_2 = f'{participant["Date_Session2"].date().strftime("%d %B")}, {calendar.day_name[participant["Date_Session2"].weekday()]}'
        time_1 = f'{participant["Timeslot_Session1"]}'
        time_2 = f'{participant["Timeslot_Session2"]}'

        body = (
            """\
            Dear """
            + name
            + """,<br><br>
            Thank you for completing the doodle poll. Based on your indicated availabilities, we have arranged your Session 2 timeslot as follows:<br><br>
            <ul>
            <strong><u>Session 1</u></strong>
            <li><strong>Date:</u> """
            + date_1
            + """</strong><br>
            <li><strong>Time:</u> """
            + time_1
            + """</strong><br>
            <li><strong>Location:</u> Nanyang Technological University (NTU), School of Humanities and School of Social Sciences (48 Nanyang Avenue)</strong><br>
            </ul><br>

            <ul>
            <strong><u>Session 2 (Day of MRI Scan)</u></strong>
            <li><strong>Date:</u> """
            + date_2
            + """</strong><br>
            <li><strong>Time:</u> """
            + time_2
            + """</strong><br>
            <li><strong>Location:</u> Nanyang Technological University (NTU), School of Humanities and School of Social Sciences (48 Nanyang Avenue)</strong><br>
            </ul><br>
            Would these arrangements work for you? Do let us know as soon as possible and we will provide you with more details in preparation for the research experiment.<br>
            Thank you and take care!<br>
            <br>
            Regards<br>
            Research Team<br>
            Clinical Brain Lab<br>
            """
        )

        message.attach(MIMEText(body, "html"))
        email_text = message.as_string()
        try:
            if to_send:
                server.sendmail(from_email, to_email, email_text)
        except Exception as e:
            retry_list.append(participant)
            continue

    return retry_list


# =============================================================================
# Send Eligibility Information
# =============================================================================
def send_inform_eligible(participants_list, message_type="pass", to_send=False):
    """Send eligibility outcome (message_type='pass' or 'fail') to participants
    """

    retry_list = []

    # Retrieve participants
    if message_type == "pass":
        participants = target_eligibility(participants_list, silent=True)[0]
    elif message_type == "fail":
        participants = target_eligibility(participants_list, silent=True)[1]

    # prepare server
    from_email = secret.gmail_name
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Prepare email structure and content for sending
    for index, participant in participants.iterrows():
        to_email = participant["Email"]  # activate when ready

        message = MIMEMultipart("alternative")
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = f"[ELIGIBILITY] Participation in Experimental Paradigm"

        # Formatted text to be insertted
        name = f'{participant["Name"]}'

        # Main body of text
        if message_type == "pass":
            body = (
                """\
                Dear """
                + name
                + """,<br><br>
                Thank you for <strong>completing the screening questionnaire</strong> for the study titled 'Experimental Paradigm' (IRB NUMBER).<br><br>
                We are glad to inform you that you are <strong><u>eligible</u></strong> to participate in this study!<br><br>
                We are in the process of confirming the session slots for this study. Once new session slots are available, we will inform you as soon as possible. We appreciate your patience!<br><br>
                Please feel free to contact us at insertemailhere@gmail.com should you have any queries.<br><br>
                Thank you!<br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab
                """
            )
        elif message_type == "fail":
            body = (
                """\
                Dear """
                + name
                + """,<br><br>
                Thank you for <strong>completing the screening questionnaire</strong> for the study titled 'Experimental Paradigm' (IRB NUMBER).<br><br>
                Unfortunately, you are <strong><u>not eligible</u></strong> for this study as you do not meet the study criteria. Once again, we thank you for your interest!<br><br>
                Please feel free to contact us at insertemailhere@gmail.com should you have any queries.<br><br>
                Thank you!<br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab
                """
            )

        message.attach(MIMEText(body, "html"))
        email_text = message.as_string()
        try:
            if to_send:
                server.sendmail(from_email, to_email, email_text)
        except Exception as e:
            retry_list.append(participant)
            continue

    return retry_list


# =============================================================================
# Types of Reminder Emails
# =============================================================================


def send_session_reminder(participants_list, message_type="Session 1", to_send=False):
    """Send different session reminders one day before the respective sessions"""
    retry_list = []

    # prepare server
    from_email = secret.gmail_name

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Session 1 Reminders
    if message_type == "Session 1":
        participants = target_participants(
            participants_list, send_when="one day before", silent=True
        )[0]

    # Session 2 Reminders
    elif message_type == "Session 2":
        participants = target_participants(
            participants_list, send_when="one day before", silent=True
        )[1]

    # Prepare email structure and content for sending
    for index, participant in participants.iterrows():
        to_email = participant["Email"]

        message = MIMEMultipart("alternative")
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = (
            f"[{message_type}".upper()
            + " REMINDER] Participation in Experimental Paradigm"
        )

        # Formatted text to be insertted
        name = f'{participant["Participant Name"]}'
        phone = f'{participant["Phone"]}'

        date_1_format = datetime.datetime.strptime(
            participant["Date_Session1"], "%d/%m/%Y"
        ).date()
        date_2_format = datetime.datetime.strptime(
            participant["Date_Session2"], "%d/%m/%Y"
        ).date()
        date_1 = f'{date_1_format.strftime("%d %B")}, {calendar.day_name[date_1_format.weekday()]}'
        date_2 = f'{date_2_format.strftime("%d %B")}, {calendar.day_name[date_2_format.weekday()]}'

        #        date_1 = f'{participant["Date_Session1"].date().strftime("%d %B")}, {calendar.day_name[participant["Date_Session1"].weekday()]}'
        #        date_2 = f'{participant["Date_Session2"].date().strftime("%d %B")}, {calendar.day_name[participant["Date_Session2"].weekday()]}'
        time_1 = f'{participant["Timeslot_Session1"]}'
        time_2 = f'{participant["Timeslot_Session2"]}'
        location_1 = f'{participant["Location_Session1"]}'
        location_2 = f'{participant["Location_Session2"]}'

        # Main body of text
        if message_type == "Session 1":
            body = (
                """\
                Dear """
                + name
                + """,<br><br>
                We are writing to remind you about your Session 1 slot on ‘Experimental Paradigm’ tomorrow. We would like to confirm with you that you are coming for Session 1 tomorrow at: <br>
                <ul>
                <li><strong><u>Time:</u> """
                + time_1
                + """</strong><br>
                <li><strong><u>Date:</u> """
                + date_1
                + """</strong><br>
                <li><strong><u>Location:</u> Nanyang Technological University (NTU), School of Humanities and School of Social Sciences (48 Nanyang Avenue), """
                + location_1
                + """</strong><br>
                </ul><br><br>
                OTHER TEXT HERE <br>
                <br>
                Regards<br>
                Research Team<br>
                Clinical Brain Lab<br>
                """
            )

        elif message_type == "Session 2":
            body = (
                """\
                Dear """
                + name
                + """,<br><br>
                This email is to remind you about your Session 2 on ‘Experimental Paradigm’ tomorrow. We will like to confirm with you that you are coming for Session 2 tomorrow at <br>
                <ul>
                <li><strong><u>Time</u>: """
                + time_2
                + """</strong><br>
                <li><strong><u>Date</u>: """
                + date_2
                + """</strong><br>
                <li><strong><u>Location</u>: Nanyang Technological University (NTU), School of Humanities and School of Social Sciences (48 Nanyang Avenue), """
                + location_2
                + """</strong>
                </ul><br><br>
                OTHER TEXT HERE <br>
                <br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab<br>
                """
            )

        message.attach(MIMEText(body, "html"))
        email_text = message.as_string()
        try:
            if to_send:
                server.sendmail(from_email, to_email, email_text)
        except Exception as e:
            retry_list.append(participant)
            continue

    return retry_list


def send_declaration_form(participants_list, message_type="Session 1", to_send=False):
    """Health and travel declaration forms to be sent on the morning of each session"""
    retry_list = []

    # prepare server
    from_email = secret.gmail_name
    #    to_email = secret.gmail_address

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    # Session 1 Reminders
    if message_type == "Session 1":
        participants = target_participants(
            participants_list, send_when="experiment day", silent=True
        )[0]

    # Session 2 Reminders
    elif message_type == "Session 2":
        participants = target_participants(
            participants_list, send_when="experiment day", silent=True
        )[1]

    # Prepare email structure and content for sending
    for index, participant in participants.iterrows():
        to_email = participant["Email"]  # activate when ready

        message = MIMEMultipart("alternative")
        message["From"] = from_email
        message["To"] = to_email
        message["reply-to"] = from_email
        message["Subject"] = (
            f"[{message_type}".upper()
            + " REMINDER] Health Declaration Form for Completion"
        )

        # Formatted text to be insertted
        name = f'{participant["Participant Name"]}'

        # Main body of text
        if message_type == "Session 1":
            body = (
                """\
                Dear """
                + name
                + """,<br><br>
                Before you come to NTU for Session 1 of the Experimental Paradigm today, please kindly complete and submit this <strong>health and travel declaration
                form</strong> by <a href="https://ntuhss.az1.qualtrics.com/jfe/form/SV_9KuYYtnwXhFd1lj">clicking here</a>.<br><br>
                All participants will have to complete this form as part of the COVID-19 safety measures.<br><br>
                Thank you for your understanding!<br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab
                """
            )
        elif message_type == "Session 2":
            body = (
                """\
                Dear """
                + name
                + """,<br><br>
                Before you come to NTU for Session 2 of Experimental Paradigm today, please kindly complete and submit this <strong>health and travel declaration
                form</strong> by <a href="http://ntuhss.az1.qualtrics.com/jfe/form/SV_2mdgszCCaZQixZr">clicking here</a>.<br><br>
                All participants will have to complete this form as part of the COVID-19 safety measures.<br><br>
                Thank you for your understanding!<br><br>
                Regards,<br>
                Research Team<br>
                Clinical Brain Lab
                """
            )

        message.attach(MIMEText(body, "html"))
        email_text = message.as_string()
        try:
            if to_send:
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

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    today = datetime.datetime.now().strftime("%x")

    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Cc"] = cc_email
    message[
        "Subject"
    ] = "ERROR: An error occured with the reminder email system ({today})."

    body = (
        "There was an error while trying to email participants.\n\n"
        "Here is the error text:\n\n"
        f"{repr(e)}"
    )

    message.attach(MIMEText(body))
    email_text = message.as_string()

    server.sendmail(from_email, [to_email] + [cc_email], email_text)


def send_success():
    from_email = secret.gmail_name
    to_email = secret.gmail_address

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(secret.gmail_address, secret.gmail_password)

    today = datetime.datetime.now().strftime("%x")

    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message[
        "Subject"
    ] = f"The Reminder Email System finished executing successfully ({today})."

    body = "No errors occured while sending emails.\n"

    message.attach(MIMEText(body))
    email_text = message.as_string()

    server.sendmail(from_email, to_email, email_text)


# =============================================================================
# Wrapper for emails
# =============================================================================


def autoremind(
    silent=False,
    send_research=False,
    send_eligible=False,
    send_confirmation=False,
    send_reminders=False,
    send_forms=False,
):
    """Autoremind wrapper

    Choose the type of emails to send or send all types by setting parameters to True.

    Parameters
    ----------
    send_research : bool
        If True, extracts unread emails and their addresses, and sends research recruitment information to them.
        Note: This will automatically mark all unread emails in your gmail as read.
    send_eligible : bool
        If True, sends information about eligibility to eligible and non-eligible participants.
    send_reminders : bool
        If True, sends reminder emails to scheduled participants one day before their experiment day.
        Note: this script will have to be run one day before their experiment.
    send_forms : bool
        If True, sends reminder emaisl to scheduled participants on the day of their experiment day.
        Note: this script will have to be run on the day of their experiment.
    silent : bool
        Prints feedback on number of individuals contacted for `send_eligible`, `send_reminders` and `send_forms`.

    Returns
    -------
    retry_total : list
        A list of participants (and their particulars) whose emails were unsuccessfully sent to.
    """
    retry_total = []

    value = input(
        "Please type 'send' to execute AutoRemind. Type anything else to only get printed feedback on participants receiving the emails."
    )
    to_send = False
    if value == "send":
        to_send = True
        print("Sending...")
    else:
        print("Skip sending...")

    # Send research info
    if send_research:
        new_addresses = get_new()
        print("Retrieving unread emails")

        retry_list = send_researchinfo(new_addresses, to_send=to_send)
        print("Research recruitment information to: " + f"{new_addresses}")
        retry_total.append(retry_list)

    if send_eligible or send_reminders or send_forms or send_confirmation:
        participants_list = get_participants()
        print("Retrieving participants particulars")

    # Send eligibility
    if send_eligible:
        n_pass, n_fail = target_eligibility(participants_list, silent=silent)
        if len(n_pass) != 0:
            retry_list = send_inform_eligible(participants_list, message_type="pass", to_send=to_send)
            retry_total.append(retry_list)
            print("Successful eligibility outcome to: " + f'{list(n_pass["Name"])}')
        if len(n_fail) != 0:
            retry_list = send_inform_eligible(participants_list, message_type="fail", to_send=to_send)
            print("Unsuccessful eligibility outcome to: " + f'{list(n_fail["Name"])}')
            retry_total.append(retry_list)

    # Send session confirmation
    if send_confirmation:
        n_confirm = target_confirmation(participants_list, silent=silent)
        retry_list = send_session_confirmation(participants_list, to_send=to_send)
        print(
            "Confirmation of session slots to: "
            + f'{list(n_confirm["Participant Name"])}'
        )
        retry_total.append(retry_list)

    # Send one-day-prior reminders
    if send_reminders:
        daybefore_session1, daybefore_session2 = target_participants(
            participants_list, send_when="one day before", silent=silent
        )
        if len(daybefore_session1) != 0:
            retry_list = send_session_reminder(
                participants_list, message_type="Session 1", to_send=to_send
            )
            print(
                "Reminder emails to: "
                + f'{list(np.array(daybefore_session1["Participant Name"]))}'
            )
            retry_total.append(retry_list)
        if len(daybefore_session2) != 0:
            retry_list = send_session_reminder(
                participants_list, message_type="Session 2", to_send=to_send
            )
            print(
                "Reminder emails to: "
                + f'{list(np.array(daybefore_session2["Participant Name"]))}'
            )
            retry_total.append(retry_list)

    # Send health declaration forms on morning of experiment day
    if send_forms:
        actual_session1, actual_session2 = target_participants(
            participants_list, send_when="experiment day", silent=silent
        )
        if len(actual_session1) != 0:
            retry_list = send_declaration_form(
                participants_list, message_type="Session 1", to_send=to_send
            )
            print(
                "Health and travel declaration forms to: "
                + f'{list(np.array(actual_session1["Participant Name"]))}'
            )
            retry_total.append(retry_list)
        if len(actual_session2) != 0:
            retry_list = send_declaration_form(
                participants_list, message_type="Session 2", to_send=to_send
            )
            print(
                "Health and travel declaration forms to: "
                + f'{list(np.array(actual_session2["Participant Name"]))}'
            )
            retry_total.append(retry_list)

    return retry_total


# =============================================================================
# Execute
# =============================================================================


def main():

    # Run this only when ready!
    retry_total = autoremind(
        silent=False,
        send_research=False,
        send_eligible=False,
        send_confirmation=False,
        send_reminders=True,
        send_forms=False,
    )

    count = 0
    emails_resend = []
    for i in retry_total:
        count += len(i)
        if len(i) != 0:
            emails_resend.append(i[0]["Email"])

    if count != 0:
        print(
            f"{count}"
            + " subjects could not be reached. Try manually sending to "
            + f"{emails_resend}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_error(e)
        print("There has been an error while emailing the participants.\n\n")
        raise
    else:
        send_success()
