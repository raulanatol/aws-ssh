# aws-push

Secure ssh (authorize before and revoke after connect) to aws servers

## Usage

```bash
aws-ssh [EC2-instance-ID] --user=[ec2-user] --region=[region]
aws-ssh i-123 profile --user=ubuntu --region=us-west-2
```

## Install

```bash
sudo make install
```

## Uninstall

```bash
sudo make uninstall
```

## Prerequisites

- [AWS Command Line Interface](https://aws.amazon.com/cli/)