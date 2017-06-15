#!/usr/bin/env python
from ec2 import EC2Instance
import boto3
import os

################################################################################
############################ LOGGING CONFIGURATION #############################
################################################################################

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EC2 Manager')

logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

################################################################################
############################## SLACK INTEGRATION ###############################
################################################################################

import requests
import json
slack_token=os.getenv('SLACK_TOKEN')
def slackpost(message):
    url = 'https://hooks.slack.com/services/' + slack_token
    headers = {
        'user-agent': 'ec2-scheduler',
        'content-type': 'application/json'
    }
    payload = {
        'username': 'Schedulebot',
        'icon_emoji': ':robot_face:',
        'message': 'Changes have been made to the AWS infrastructure.',
        'mrkdwn': True,
        'attachments': [
            {
                'pretext': 'Changes have been made to the AWS infrastructure.',
                'color': '#78D0DE',
                'text': message,
                'mrkdwn_in': [
                    'text',
                    'pretext'
                ]
            }
        ]
    }
    slack = requests.post(url, data=json.dumps(payload), headers=headers)
    if slack.status_code == 200:
        logger.info('Submitted results via Slack.')
    else:
        logger.error('Failed to send message to Slack!')
    return

################################################################################
############################## CHANGES REPORTING ###############################
################################################################################

# In order to track changes made we'll populate a dictionary of changes
changes = {
    'started': [],
    'stopped': [],
    'terminated': []
}

def report():
    """ Generates simple report of changes made during run """
    response = ''
    if changes['started']:
        response += '*The following instances were started:*\n'
        results = []
        for instance in changes['started']:
            text = '%s *(%s)*' % (instance.properties['Name'], instance.id)
            results.append(text)
        response += '\n'.join(results) + '\n'
    if changes['stopped']:
        response += '*The following instances were stopped:*\n'
        results = []
        for instance in changes['stopped']:
            text = '%s *(%s)*' % (instance.properties['Name'], instance.id)
            results.append(text)
        response += '\n'.join(results) + '\n'
    if changes['terminated']:
        response += '*The following instances were terminated:*\n'
        results = []
        for instance in changes['terminated']:
            text = '%s *(%s)*' % (instance.properties['Name'], instance.id)
            results.append(text)
        response += '\n'.join(results) + '\n'
    if len(response) == 0:
        response = False
    return response

################################################################################
################################## FUNCTIONS ###################################
################################################################################

def checkSchedule(EC2Instance):
    """ Checks machine schedule and carries out power on/shutdown action """
    if EC2Instance.managed:
        if EC2Instance.state['Name'] == 'stopped' and EC2Instance.scheduled:
            EC2Instance.start()
            changes['started'].append(EC2Instance)
            logger.info('%s - Instance started - %s' % (EC2Instance.id, EC2Instance.properties['Name']))
        elif EC2Instance.state['Name'] == 'running' and not EC2Instance.scheduled:
            EC2Instance.stop()
            changes['stopped'].append(EC2Instance)
            logger.info('%s - Instance stopped - %s' % (EC2Instance.id, EC2Instance.properties['Name']))
    return None

def checkCreator(EC2Instance):
    """ Updates creator field if possible """
    if EC2Instance.properties['Creator'] == 'unknown':
        creator = EC2Instance.creator()
        logger.warn('%s - Creator information incorrect - %s' % (EC2Instance.id, EC2Instance.properties['Name']))
        if creator:
            logger.info('%s - Created by %s - %s' % (EC2Instance.id, creator, EC2Instance.properties['Name']))
            EC2Instance.properties['Creator'] = creator
            EC2Instance.update()
    return None

def checkExpires(EC2Instance):
    """ Checks if machines have expired and then terminates them """
    if EC2Instance.expired:
        EC2Instance.properties['Tag'] = 'Value'
        logger.warn('%s - Instance expired - %s' % (EC2Instance.id, EC2Instance.properties['Name']))
        # EC2Instance.terminate()
        changes['terminated'].append(EC2Instance)
        logger.warn('%s - Instance terminated - %s' % (EC2Instance.id, EC2Instance.properties['Name']))
    return None


################################################################################
################################### RUNTIME ####################################
################################################################################

if __name__ == '__main__':
    logger.info('Scheduler started.')
    # Create connection to AWS
    ec2 = boto3.resource('ec2')
    # Create instances iterable
    instances = ec2.instances.all()
    # Instance loop
    for instance in instances:
        if not instance.state['Name'] == 'terminated':
            logger.info('%s - Inspecting instance...' % instance.id)
            i = EC2Instance(instance)
            checkExpires(i)
            checkCreator(i)
            checkSchedule(i)
    logger.info('Scheduler completed.')
    result = report()
    if result and slack_token:
        slackpost(result)
