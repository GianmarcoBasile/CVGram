@echo off
for %%R in (master workers) do (
    for /f "delims=" %%I in ('jq -r ".%%R.instance_id" ..\ec2.json') do set INSTANCE_ID=%%I
    for /f "delims=" %%A in ('jq -r ".%%R.allocation_id" ..\ec2.json') do set ALLOCATION_ID=%%A

    aws ec2 stop-instances --instance-ids %INSTANCE_ID% --region eu-west-2
    echo Istanza EC2 %INSTANCE_ID% stoppata

    aws ec2 disassociate-address --allocation-id %ALLOCATION_ID% --region eu-west-2
    aws ec2 release-address --allocation-id %ALLOCATION_ID% --region eu-west-2
    echo Elastic IP %ALLOCATION_ID% disassociato e rilasciato
)