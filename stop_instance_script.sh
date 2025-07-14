#!/bin/bash

for role in master workers; do
    INSTANCE_ID=$(jq -r ".${role}.instance_id" ../ec2.json)
    ALLOCATION_ID=$(jq -r ".${role}.allocation_id" ../ec2.json)

    aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --region eu-west-2
    echo "Istance EC2 $INSTANCE_ID stoppata"

    aws ec2 disassociate-address --allocation-id "$ALLOCATION_ID" --region eu-west-2
    aws ec2 release-address --allocation-id "$ALLOCATION_ID" --region eu-west-2
    echo "Elastic IP $ALLOCATION_ID disassociato e rilasciato"
done