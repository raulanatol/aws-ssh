#!/usr/bin/env python
import subprocess
import requests
import boto3
import logging
import re
import os

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
validate_ip = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def get_public_ip():
    res = requests.get('http://ipecho.net/plain')
    if not validate_ip.match(res.text):
        raise RuntimeError('Error getting the client public ip: ', res.text)
    return res.text + '/32'


def get_ip_permissions(port, client_ip):
    return {
        "IpProtocol": "tcp",
        "FromPort": port,
        "ToPort": port,
        "IpRanges": [
            {
                "CidrIp": client_ip
            }
        ]
    }


def authorize_ssh(client, security_group_id, client_ip):
    try:
        ip_permissions = [get_ip_permissions(22, client_ip)]
        client.authorize_security_group_ingress(GroupId=security_group_id, IpPermissions=ip_permissions)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            pass
        else:
            raise e


def revoke_ssh(client, security_group_id, client_ip):
    ip_permissions = [get_ip_permissions(22, client_ip)]
    client.revoke_security_group_ingress(GroupId=security_group_id, IpPermissions=ip_permissions)


def open_ssh(key_pair_file, user, ip):
    custom_ssh = ['ssh', '-i', key_pair_file]
    custom_ssh.extend([user + '@' + ip])

    logging.info('Running ' + ' '.join(custom_ssh))
    return_code = subprocess.call(custom_ssh)
    if return_code != 0:
        logging.info(custom_ssh[0] + ' returned exitcode: ' + str(return_code))
        raise RuntimeError('An error occurred while running: ' + custom_ssh[0] + '.')


def do_ssh(client, instance_id, key_pair_file, user):
    client_ip = get_public_ip()
    instances = client.describe_instances(InstanceIds=[instance_id])
    if len(instances['Reservations']) < 1:
        raise RuntimeError('No instances found')
    if len(instances['Reservations'][0]['Instances']) < 1:
        raise RuntimeError('No instances found')
    instance = instances['Reservations'][0]['Instances'][0]
    if len(instance['SecurityGroups']) < 1:
        raise RuntimeError('No security groups found')

    # Get key_pair_file if null
    if not key_pair_file:
        key_pair_file = get_key_pair_filename(instance)

    group_id = instance['SecurityGroups'][0]['GroupId']
    ip = instance['PublicIpAddress']

    authorize_ssh(client, group_id, client_ip)
    try:
        open_ssh(key_pair_file, user, ip)
    except OSError:
        RuntimeError('Error trying to open ssh connection')
    finally:
        revoke_ssh(client, group_id, client_ip)


def get_key_pair_filename(instance):
    pair_name = instance['KeyName']
    sep = os.path.sep
    ssh_folder = '~' + sep + '.ssh' + sep
    ssh_folder = os.path.expanduser(ssh_folder)
    if not os.path.exists(ssh_folder):
        os.makedirs(ssh_folder)
    key_file = ssh_folder + pair_name
    if os.path.exists(key_file + '.pem'):
        key_file += '.pem'
    else:
        raise RuntimeError('SSH file not found: ', key_file)
    return key_file


def ssh_command(mode='profile', instance=None, profile=None, key=None, user='ec2-user', region='us-west-1', access=None, secret=None):
    """
    Secure ssh connection with ec2 server

    :param mode: profile or key_modes
    :param instance: The instance id to connect
    :param profile: aws profile name
    :param key: .pem file to connect
    :param user: The unix instance user
    :param region: Amazon region of instance to connect
    :param access: AccessKeyId
    :param secret: SecretAccessKey
    """

    if mode == 'profile':
        session = boto3.Session(profile_name=profile, region_name=region)
        client = session.client('ec2')
    else:
        client = boto3.client('ec2', aws_access_key_id=access, aws_secret_access_key=secret, region_name=region)

    do_ssh(client, instance, key, user)


if __name__ == '__main__':
    import scriptine

    scriptine.run()
