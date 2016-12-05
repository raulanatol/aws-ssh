#!/usr/bin/env python
import subprocess
import requests
import os

from cement.utils.misc import minimal_logger
from ebcli.lib.ec2 import describe_instance
from ebcli.lib.aws import set_profile, set_region, make_api_call
from ebcli.resources.strings import strings, responses
from ebcli.objects.exceptions import ServiceError, NoKeypairError, NotFoundError, CommandError
from ebcli.core import io, fileoperations

LOG = minimal_logger(__name__)


def get_public_ip():
    res = requests.get('http://ipecho.net/plain')
    return res.text + '/32'


def _make_api_call(operation_name, **operation_options):
    return make_api_call('ec2', operation_name, **operation_options)


def _get_ssh_file(keypair_name):
    key_file = fileoperations.get_ssh_folder() + keypair_name
    if not os.path.exists(key_file):
        if os.path.exists(key_file + '.pem'):
            key_file += '.pem'
        else:
            raise NotFoundError(strings['ssh.filenotfound'].replace(
                '{key-name}', keypair_name))

    return key_file


def authorize_ssh(security_group_id, client_ip):
    try:
        _make_api_call('authorize_security_group_ingress',
                       GroupId=security_group_id, IpProtocol='tcp',
                       ToPort=22, FromPort=22, CidrIp=client_ip)
    except ServiceError as e:
        if e.code == 'InvalidPermission.Duplicate':
            pass
        else:
            raise


def revoke_ssh(security_group_id, client_ip):
    try:
        _make_api_call('revoke_security_group_ingress',
                       GroupId=security_group_id, IpProtocol='tcp',
                       ToPort=22, FromPort=22, CidrIp=client_ip)
    except ServiceError as e:
        if e.message.startswith(responses['ec2.sshalreadyopen']):
            # ignore
            pass
        else:
            raise


def do_ssh(keypair_name, user, ip):
    ident_file = _get_ssh_file(keypair_name)
    custom_ssh = ['ssh', '-i', ident_file]
    custom_ssh.extend([user + '@' + ip])

    io.echo('INFO: Running ' + ' '.join(custom_ssh))
    returncode = subprocess.call(custom_ssh)
    if returncode != 0:
        LOG.debug(custom_ssh[0] + ' returned exitcode: ' + str(returncode))
        raise CommandError('An error occurred while running: ' + custom_ssh[0] + '.')


def ssh_command(instance_id, profile, user='ec2-user', region='us-west-1'):
    """
    Secure ssh connection with ec2 server

    :param instance_id: The instance id to connect
    :param profile: aws profile name
    :param user: The unix instance user
    :param region: Amazon region of instance to connect
    """

    if profile:
        set_profile(profile)
    set_region(region)
    client_ip = get_public_ip()
    # TODO verify if valid public ip
    instance = describe_instance(instance_id)
    try:
        keypair_name = instance['KeyName']
    except KeyError:
        raise NoKeypairError()

    try:
        ip = instance['PublicIpAddress']
    except KeyError:
        raise NotFoundError(strings['ssh.noip'])

    security_groups = instance['SecurityGroups']
    # TODO verify length
    group = security_groups[0]
    group_id = group['GroupId']

    io.echo(strings['ssh.openingport'])
    authorize_ssh(group_id, client_ip)
    io.echo(strings['ssh.portopen'])

    try:
        do_ssh(keypair_name, user, ip)
    except OSError:
        CommandError(strings['ssh.notpresent'])
    finally:
        revoke_ssh(group_id, client_ip)
        io.echo(strings['ssh.closeport'])


if __name__ == '__main__':
    import scriptine

    scriptine.run()
