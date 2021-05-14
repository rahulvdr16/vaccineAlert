#!/usr/bin/python3
'''
Make sure these environment variables are set:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID

The cowin api webiste says:
The appointment availability data is cached and may be upto 30 minutes old.
Further, these APIs are subject to a rate limit of 100 API calls per 5 minutes per IP.
Please consider these points while using the APIs in your application.
Dated : 13 May 14:35

'''
import os
import requests
from requests.exceptions import ConnectionError, Timeout
import time
import schedule
import argparse
import sys
import platform # To detect the OS
import subprocess

def testConnection():
    '''
    Function to test if there is an active internet connection.
    '''
    url = 'https://www.google.com'
    try:
        r = requests.get (url)
    except ConnectionError:
        print ('Network Connection Error.')
        exit()
    except Timeout:
        print ('Taking too long to connect.')
        return None


class TelegramSender:
    '''
    Sender class to handle sending messages from the Telegram bot.
    telegramToken: API token of the Telegram bot
    chatID: chat ID of the contact to which to send the message.
    '''
    baseUrl = 'https://api.telegram.org/bot'
    def __init__(self, token, chatID):
        self.telegramToken = token
        self.chatID = chatID
        
    def sendMessage(self, message, chat_id = None, telegram_token = None):
        if chat_id is None:
            chat_id = self.chatID
        if telegram_token is None:
            telegram_token = self.telegramToken

        data = {'text': message, 'chat_id': chat_id}
        response = requests.post (self.baseUrl + telegram_token + '/sendMessage', data = data)
        return response.json()

# sender = TelegramSender (os.environ.get ('TELEGRAM_BOT_TOKEN'), os.environ.get ('TELEGRAM_CHAT_ID'))

class EmailSender:
    '''
    Class to handle email alerts.
    '''
    # To be added when adding email functionality
    pass

class WhatsappSender:
    '''
    Class to handle Whatsapp alerts.
    '''
    # to be added when adding whatsapp alerts functionality
    pass

class sendDesktopNotification:
    '''
    Class to handle desktop notifications / alerts.
    # to-do:
    Improve the code to detect the os and use the appropriate functions.
    '''
    def __init__ (self):
        if platform.system() == 'Linux':
            self.os = 'linux'
            self.notify = self.notify_in_linux
        elif platform.system() == 'Darwin':
            self.os = 'macos'
            self.notify = self.notify_in_macos
        elif platform.system() == 'windows':
            self.os = 'windows'
            self.notify = self.notify_in_windows

    def notify(self, messageTitle, message):
        '''
        Main function to send the desktop notification.
        '''
        if self.os == 'linux':
            self.notify_using_notifySend (self, messageTitle, message)
        elif self.os == 'macos':
            self.notify_for_macos (self, messageTitle, message)
        pass
    def notify_in_linux(self, messageTitle, message):
        '''
        Uses the notify-send utility in ubuntu to send desktop notifications / alerts.
        '''
        subprocess.Popen (['notify-send', '-u', 'critical', '-i', 'notification-message-IM', messageTitle, message])

    def notify_in_macos (self, messageTitle, message):
        '''
        Notification function for MacOS.
        '''
        pass

    def notify_in_windows (self, messageTitle, message):
        '''
        Notification function for windows os.
        '''
        pass

class CowinAPIHandler:
    '''
    Handler class to handle the API requests to cowin/APIsetu api.
    Using api from this link :
    https://apisetu.gov.in/public/marketplace/api/cowin
    '''
    baseUrl = 'https://cdn-api.co-vin.in/api'

    def __init__ (self, headers = None):
        if headers is None:
            self.headers = {'User-Agent': 'Mozilla/5.0 (Linux; ; ) AppleWebKit/ (KHTML, like Gecko) Chrome/ Mobile Safari/'}
            # Just a dummy user agent. The API seems to return network error if not provided with a header.
        pass

    def findAppointmentsByPin(self, pin: str, date: str):
        '''
        Get planned vaccination sessions on a specific date in a given place (pincode).
        '''
        endpointUrl = '/v2/appointment/sessions/public/findByPin'
        params = {'Accept-Language': 'hi_IN', 'pincode': str (pin), 'date': str (date)}
        r = requests.get (self.baseUrl + endpointUrl, params = params, headers = self.headers)
        return r.json()

    def isAppointmentAvailable_byPin (self, pin: str, date: str) -> bool:
        '''
        Retuns true if open slots / appointments are available for the location given by pincode.
        '''
        sessions = self.findAppointmentsByPin ( str (pin), str (date))
        if len (sessions['sessions']) == 0:
            return False
        
        # To-do:
        # Look at the schema, try with an example and scrape the details.


    def findAppointmentsByDistrict (self, district_id: str, date: str):
        '''
        Get planned vaccination sessions on a specific date in a given district.
        district_id : district specified by district id
        date : date as a string as DD-MM-YYYY
        '''
        endpointUrl = '/v2/appointment/sessions/public/findByDistrict'
        params = {'Accept-Language': 'hi_IN', 'district_id': str (district_id), 'date': str (date) }
        r = requests.get (self.baseUrl + endpointUrl, params = params, headers = self.headers)
        return r.json()

    def isAppointmentAvailable_byDistrict (self, district_id: str, date: str) -> bool:
        '''
        Returns True if there is an appointment available.
        '''
        sessions = findAppointmentByDistrict ( str (district_id), str (date) )
        if len (sessions['sessions']) == 0:
            return False
        # To-do:
        # check the function

    def calendarByPin (self, pin: str, date: str):
        '''
        Get planned vaccination sessions for 7 days from a specific date in a given pin.
        '''
        endpointUrl = '/v2/appointment/sessions/public/calendarByPin'
        params = {'Accept-Language': 'hi_IN', 'pincode': str (pin), 'date': str (date)}
        r = requests.get (self.baseUrl + endpointUrl, params = params, headers = self.headers)
        return r.json()

    def calendarByDistrict (self, district_id: str, date: str):
        '''
        Get planned vaccination sessions for 7 days from a specific date in a given district.
        '''
        endpointUrl = '/v2/appointment/sessions/public/calendarByDistrict'
        params = {'Accept-Language': 'hi_IN', 'district_id': str (district_id), 'date': str (date)}
        r = requests.get (self.baseUrl + endpointUrl, params = params, headers = self.headers)
        return r.json()

    def isAvailableThisWeek_byPin(self, pin: str, date: str) -> (bool, list):
        '''
        Returns true if there is an appointment available the coming week in a given place ( pincode )
        '''
        r = self.calendarByPin ( str (pin), str (date))
        centers = r['centers']
        for center in centers:
            sessions = center['sessions']
            for session in sessions:
                if session['available_capacity'] > 0:
                    return (True, centers)
        return (False, None)

    def isAvailableThisWeek_byDistrict (self, district_id: str, date: str) -> (bool, list):
        '''
        Returns true if there is an appointment available the coming week in a given district.
        '''
        r = self.calendarByDistrict ( str (district_id), str (date))
        centers = r['centers']
        for center in centers:
            sessions = center ['sessions']
            for session in sessions:
                if session ['available_capacity'] > 0:
                    return (True, centers)
        return (False, None)

def checkForAppointments():
    '''
    Calls the required functions to check if any appointments are available.
    '''
    pass
def checkForAppointments_byPin():
    '''
    '''
    pass

def checkForAppointments_byDistrict():
    '''
    '''
    pass

def testbypin (pin: str, date: str):
    '''
    Test the polling functionality by checking availability for a given pin
    '''
    cowin_api_handler = CowinAPIHandler()
    availability, centers = cowin_api_handler.isAvailableThisWeek_byPin (pin, date)
    global sender
    global desktopNotifier
    if availability:
        message = f"There are slots available this week.\n{time.ctime()}"
        sender.sendMessage (message)
        desktopNotifier.notify ('Vaccine Alert', message)
    # To-do:
    # Include center details in the message.

##############################

#  Declare the alert objects

##############################

desktopNotifier = sendDesktopNotification()
sender = TelegramSender (os.environ.get ('TELEGRAM_BOT_TOKEN'), os.environ.get ('TELEGRAM_CHAT_ID'))

def main():
    parser = argparse.ArgumentParser (description = 'Script to send an alert when there is covid vaccine slot available.')
    parser.add_argument ('-P', '--pin', help = 'Pincode of your place.', required = 'True')
    pin = parser.parse_args (sys.argv[1:]).pin
    try:
        schedule.every(1).minutes.do (testbypin, pin = pin, date = time.strftime("%d-%m-%Y", time.localtime()))
        while True:
            schedule.run_pending()
    except ConnectionError:
        print ('Network connection error. Check your internet connection.')
        exit()
    except KeyboardInterrupt:
        print ('Exiting from the script..')
        exit()


def testSender():
    '''
    Test function to test Telegram notification functionality.
    '''
    sender = TelegramSender(os.environ.get ('TELEGRAM_BOT_TOKEN'), os.environ.get ('TELEGRAM_CHAT_ID'))
    message = 'This is a test message.' + 'Time: ' + str(time.ctime())
    r = sender.sendMessage (message)
    print (r)

if __name__ == '__main__':
    main()
