#!/usr/bin/env python
import boto3
from datetime import datetime

class EC2Instance(object):
    """ High-level interface to manage EC2 instances """

    def __init__(self, obj):
        self.obj = obj
        self.properties = {}
        self.expires = False
        self.expired = False
        self.managed = False
        self.scheduled = True
        self.validate()
        self._checkExpires()
        self._checkManaged()
        self._checkScheduled()

    # Inherit object attributes from original EC2 object
    def __getattr__(self, name):
        return getattr(self.__dict__['obj'], name)

    def creator(self):
        """ Investigates who created the instance from CloudTrail """
        creator = None
        # Define search parameters
        search = [{'AttributeKey': 'EventName', 'AttributeValue': 'RunInstances'}]

        # Create connection to AWS and update tags.
        client = boto3.client('cloudtrail')
        results = client.lookup_events(LookupAttributes=search, MaxResults=50)

        # Look through all results for events matching the instance ID.
        for event in results['Events']:
            found = list(resource for resource in event['Resources'] if resource['ResourceName'] == self.id)
            creator = event['Username']
            return creator

        return creator

    def update(self):
        """ Update tags on AWS from self.properties """

        # Generate AWS compatible list of tag objects.
        tags = []
        for key, value in self.properties.items():
            tags.append({'Key': key, 'Value': value})

        # Create connection to AWS and update tags.
        client = boto3.client('ec2')
        client.create_tags(Resources=[self.instance_id], Tags=tags)

        # Refresh local instance object to reflect changes.
        self.reload()
        return

    def validate(self):
        """ Validate keys in tags to match approved schema. """
        changes = False
        free = [
            'Name',
            'Description',
            'Creator',
            'Service',
            'Expires'
        ]
        strict = {
            'Availability': ['default', 'always', 'weekdays', 'out-of-hours', 'everyday'],
            'Environment': ['development', 'integration', 'preview', 'preproduction', 'production'],
            'Managed': ['yes', 'no']
        }

        # Populate self.properties dictionary from self.tags
        if self.tags is not None:
            for tag in self.tags:
                self.properties[tag['Key']] = tag['Value']

        # Set all free fields that are not currently defined to 'Unknown'.
        missing = list(field for field in free if field not in self.properties)
        for field in missing:
            self.properties[field] = 'unknown'
        if missing:
            changes = True

        # For strict fields, default to the first option if not compliant.
        for key, values in strict.items():
            if key not in self.properties or self.properties[key] not in values:
                self.properties[key] = values[0]
                changes = True

        # If any properties have changed, update tags.
        if changes:
            self.update()

        return

    def _checkExpires(self):
        """ Converts 'Expires' tag to datetime for self.expires """
        try:
            self.expires = datetime.strptime(self.properties['Expires'], '%Y-%m-%d-%H-%M')
            if self.expires < datetime.utcnow() and self.properties['Managed'].lower() == 'yes':
                self.expired = True
        except:
            self.expires = False
            self.expired = False
        return

    def _checkManaged(self):
        """ Converts 'Managed' tag to boolean for self.managed """
        if self.properties['Managed'].lower() == 'yes':
            self.managed = True
        else:
            self.managed = False
        return

    def _checkScheduled(self):
        """ Checks if machine is scheduled to be available """
        scheduled = True
        now = datetime.now()
        workingdays = range(0,5)
        workinghours = range(7,20)

        # Default schedules for each environment
        defaults = {
        'development':   'weekdays',
        'integration':   'weekdays',
        'preview':       'weekdays',
        'preproduction': 'always',
        'production':    'always'
        }

        # Set availability from tag if it's available.
        availability = self.properties['Availability']
        environment  = self.properties['Environment']

        # If availability is simply set as default, look up what the default
        # schedule is for that environment.
        if availability == 'default':
            availability = defaults[environment]

        # Identify if the instance should be running based on it's schedule.
        if availability == 'weekdays':
            if now.weekday() not in workingdays or now.hour not in workinghours:
                scheduled = False
        elif availability == 'out-of-hours':
            if now.weekday() in workingdays and now.hour in workinghours:
                scheduled = False
        elif availability == 'everyday':
            if now.hour not in range(7,22): # 07:00-22:00 on any day of the week.
                scheduled = False
        self.scheduled = scheduled
        return
