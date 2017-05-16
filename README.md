ec2-scheduler
=============

Simple Python script for managing EC2 instances on AWS using a strict tag schema.

## Details

When you run ec2-scheduler, it will enforce a number of tags across your EC2
instances which allow you to store metadata about the instances themselves.

When working on larger projects I've found it can sometimes be difficult to
identify why an instance exists and who created it.

Additionally for the sake of cost saving it is possible to use this same
metadata to provide a cost saving by powering down instances out-of-hours which
aren't needed for 24/7 operations.

## Instructions

You'll need to set up your AWS command line tools as you typically would. The
script relies on finding your AWS credentials in `~/.aws/credentials`.

You can set up your credentials using the [AWS documentation](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).

After that you will need to install the Python modules listed in `requirements.txt`.
It's recommended you use a Virtual Environment for the install.

You can then run the `run.py` script.

## Tag schema:
All components that make up the infrastructure conform to a tag schema. The
schema is designed to provide additional useful information about infrastructure
objects and allows for some intelligent management of services.

| Tag          | Permitted values                  | Description                   |
|--------------|-----------------------------------|-------------------------------|
| Name         | e.g. `proxy-01`                   | Name of object                |
| Description  | string                            | Free-hand description         |
| Creator      | e.g. `John Smith`                 | Person who provision object   |
| Service      | e.g. `point-of-sale`              | Service object belongs to     |
| Expires      | `never` / `YYYY-MM-DD-HH-MM`      | Date object is decommissioned |
| Availability | `always` / `weekdays` / `default` | Object availability profile   |
| Environment  | e.g `production` / `development`  | Application environment       |
| Managed      | 'true' / 'false'                  | Automated server management   |

Expires should be set to UTC dates.

## Availability:

The following schedules are available:
- `always` *instances run on 24/7 operation*
- `weekdays` *instances run between 07:00 and 20:00 Monday to Friday*
- `out-of-hours` *instances run on the opposite schedule to `weekdays`*
- `everyday` *instances run between 07:00 and 22:00 every day*
- `default` *schedule depends on environment tag*

environment:  production / preproduction / preview / integration / development  
availability: always / weekdays/ out-of-hours / default
