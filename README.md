# aws-push

Secure ssh (authorize before and revoke after connect) to aws servers

## Usage

```bash
aws-ssh ssh --instance=[EC2-instance-ID] --user=[ec2-user] --region=[region]
aws-ssh ssh --instance=[instance-id] --user=ubuntu --region=us-west-2
aws-ssh ssh --mode=key_modes --instance=[instance-id] --key=/file.pem --user=[ec2-user] --region=[region] --access=[access-key] --secret=[access-secret-key]  
```

## Install

```bash
sudo make install
```

## Uninstall

```bash
sudo make uninstall
```
