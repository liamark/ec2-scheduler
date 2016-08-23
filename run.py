#!/usr/bin/env python
from ec2 import EC2Instance
import boto3

################################################################################
############################ LOGGING CONFIGURATION #############################
################################################################################

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EC2 Manager')

logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)


################################################################################
################################## FUNCTIONS ###################################
################################################################################

def checkSchedule(EC2Instance):
    """ Checks machine schedule and carries out power on/shutdown action """
    if EC2Instance.managed:
        if EC2Instance.state['Name'] == 'stopped' and EC2Instance.scheduled:
            #EC2Instance.start()
            logger.warn('%s - Instance started to match schedule.' % EC2Instance.id)
        elif EC2Instance.state['Name'] == 'running' and not EC2Instance.scheduled:
            #EC2Instance.stop()
            logger.warn('%s - Instance stopped to match schedule.' % EC2Instance.id)
    return None

def checkCreator(EC2Instance):
    """ Updates creator field if possible """
    if EC2Instance.properties['Creator'] == 'unknown':
        creator = EC2Instance.creator()
        logger.warn('%s - Creator information incorrect.' % EC2Instance.id)
        if creator:
            logger.info('%s - Created by %s' % (EC2Instance.id, creator))
            EC2Instance.properties['Creator'] = creator
            EC2Instance.update()
    return None

def checkExpires(EC2Instance):
    """ Checks if machines have expired and then terminates them """
    if EC2Instance.expired:
        EC2Instance.properties['Tag'] = 'Value'
        logger.warn('%s - Instance expirary date has passed.' % EC2Instance.id)
        # EC2Instance.terminate()
        logger.warn('%s - Instance terminated.' % EC2Instance.id)
    return None


################################################################################
################################### RUNTIME ####################################
################################################################################

if __name__ == '__main__':
    # Create connection to AWS
    ec2 = boto3.resource('ec2')
    # Create instances iterable
    instances = ec2.instances.all()
    # Instance loop
    for instance in instances:
        i = EC2Instance(instance)
        logger.info('%s - Checking instance...' % i.id)
        checkExpires(i)
        checkCreator(i)
        checkSchedule(i)
