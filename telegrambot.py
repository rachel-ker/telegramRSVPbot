#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
from __future__ import print_function
import pickle
from auth import *
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import logging

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '15LZkHNJUfzMMKJqzG_QQe0O0O29ggiTQDFADwTPP7A8'
SAMPLE_RANGE_NAME = 'Sheet1'

def add_to_sheets(val):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

    # Call the Sheets API
    sheet = service.spreadsheets()

    body = {
        'values': val
    }

    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=SAMPLE_RANGE_NAME,
        valueInputOption='USER_ENTERED',
        body=body).execute()
    print('{0} cells updated.'.format(result['updates'].get('updatedCells')))



# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

reply_keyboard = [  ['Name', 'Affiliation', 'Attendance'], 
                    ['Email', 'Dietary Requirements'], 
                    ['Other Comments', 'Done']]
markup_allfields = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

AFFILIATION, EMAIL, DIET, SHOWDATA, CHOOSING, TYPING_REPLY = range(6)

    
def start(update, context):
    update.message.reply_text(
        "Hi, Bryan and Rachel invites you to join us at our wedding celebrations on the morning of 12.12.2020 at Bethesda Church Bukit Arang. "
        "More details on your invite! If you have questions, feel free to get in touch at @BryanLeong or @rachelker.",
        )
    return attendance(update, context)

def attendance(update, context):
    user = update.message.from_user
    logger.info("User %s started to RSVP.", user.first_name)

    attendance = [["Attending", "Not Attending"]]
    markup_attendance = ReplyKeyboardMarkup(attendance, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "Will you be joining us on 12 Dec 2020?",
        reply_markup=markup_attendance)
    
    if user.last_name:
        context.user_data['Name'] = '{} {}'.format(user.first_name, user.last_name)
    else:
        context.user_data['Name'] = user.first_name
    
    context.user_data['Username'] = user.username
    return AFFILIATION

def save_field(update, context, field):
    user = update.message.from_user
    logger.info("%s for %s saved", field, user.first_name)
    context.user_data[field] = update.message.text

def affiliation_notattending(update, context):
    # save result from attendance before moving to next
    save_field(update, context, 'Attendance')

    affiliation = [
        ["Church", "Family", "Work"],
        ["Secondary/JC Friends", "USP"],
        ["UChicago/UIUC","Social Work/Sociology"], 
        ["Volunteering", "Others"]
        ]
    markup_affiliation = ReplyKeyboardMarkup(affiliation, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "How do you know us?", reply_markup=markup_affiliation
        )
    
    return SHOWDATA

def affiliation_attending(update, context):
    # save result from attendance before moving to next
    save_field(update, context, 'Attendance')

    affiliation = [
        ["Church", "Family", "Work"],
        ["Secondary/JC Friends", "USP"],
        ["UChicago/UIUC","Social Work/Sociology"], 
        ["Volunteering", "Others"]
        ]
    markup_affiliation = ReplyKeyboardMarkup(affiliation, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "How do you know us?", reply_markup=markup_affiliation
        )
    
    return EMAIL

def email(update, context):
    save_field(update, context, 'Affiliation')

    update.message.reply_text(
        "What's your email address? We would love to drop you a confirmation.",
        reply_markup=ReplyKeyboardRemove())
    return DIET

def diet(update, context):
    save_field(update, context, 'Email')

    update.message.reply_text(
        "Any dietary requirements we should note?",
        reply_markup=ReplyKeyboardRemove()
        )
    return SHOWDATA


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def show_data(update, context):
    save_field(update, context, 'Dietary Requirements')

    logger.info("Show data")

    user_data = context.user_data
    update.message.reply_text("Awesome! This is what you have told me:\n"
                              "{}\n"
                              "Click on any field you want to change or select Done to submit.".format(facts_to_str(user_data)),
                              reply_markup=markup_allfields)
    return CHOOSING

def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    logger.info("Updating %s", text)

    if text == 'Affiliation':
        affiliation = [
        ["Church", "Family", "Work"],
        ["Secondary/JC Friends", "USP"],
        ["UChicago/UIUC","Social Work/Sociology"], 
        ["Volunteering", "Others"]
        ]
        markup_affiliation = ReplyKeyboardMarkup(affiliation, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
        "How do you know us?", reply_markup=markup_affiliation
        )
    elif text == 'Attendance':
        attendance = [["Attending", "Not Attending"]]
        markup_attendance = ReplyKeyboardMarkup(attendance, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            "Will you be joining us on 12 Dec 2020?",
            reply_markup=markup_attendance)
    
    elif text == 'Other Comments':
        reply_text = 'What else would you like us to know?'
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    
    else:
        reply_text = 'What is your updated {}?'.format(text.lower())
        update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove())
    
    return TYPING_REPLY

def update_info(update, context):
    text = update.message.text
    category = context.user_data['choice']
    context.user_data[category] = text
    del context.user_data['choice']

    update.message.reply_text("Neat! Do you want to update anything else?\n"
                              "{}".format(facts_to_str(context.user_data)),
                              reply_markup=markup_allfields)

    return CHOOSING


def done(update, context):
    logger.info("Done")

    user_data = context.user_data
    if 'choice' in context.user_data:
        del context.user_data['choice']

    update.message.reply_text("Thank you for your RSVP!\n"
                              "{}\n"
                              "See you soon!".format(facts_to_str(user_data)),
                              reply_markup=ReplyKeyboardRemove())
    
    name = user_data.get('Name')
    email = user_data.get('Email')
    diet = user_data.get('Dietary Requirements')
    comments = user_data.get('Other Comments')
    affiliation = user_data.get('Affiliation')
    username = user_data.get('Username')

    if user_data.get('Attendance')=='Attending':
        attendance = 'coming'
    else:
        attendance = 'notcoming'

    values = [[name, attendance, email, diet, comments, affiliation, username]]
    logger.info(values)
    add_to_sheets(values)

    user_data.clear()
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states = {
            AFFILIATION: [MessageHandler(Filters.regex('^(Attending)$'), affiliation_attending),
                          MessageHandler(Filters.regex('^(Not Attending)$'), affiliation_notattending),
                          ],
            EMAIL: [MessageHandler(Filters.text, email),
                    ],
            DIET: [MessageHandler(Filters.text, diet),
                   ],
            SHOWDATA: [MessageHandler(Filters.text, show_data)],
            CHOOSING: [MessageHandler(Filters.regex('^(Name|Affiliation|Attendance|Email|Dietary Requirements|Other Comments)$'), regular_choice),
                       MessageHandler(Filters.regex('^Done$'), done),
                       ],
            TYPING_REPLY: [MessageHandler(Filters.text, update_info),
                ]   

        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()