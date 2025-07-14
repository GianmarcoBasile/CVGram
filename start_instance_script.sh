#!/bin/bash

# Assicurati che awscli sia installato e configurato

INSTANCE_IDS=$(jq -r '.master.instance_id, .workers.instance_id' ../ec2.json)

for id in $INSTANCE_IDS; do
    aws ec2 start-instances --instance-ids "$id" --region eu-west-2
    echo "Avviata istanza EC2 con ID: $id"
done