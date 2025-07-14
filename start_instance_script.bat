@echo off
for /f "tokens=2 delims=:," %%A in ('findstr /i "instance_id" ..\ec2.json') do (
    set id=%%~A
    set id=!id:"=!
    call :start_instance !id!
)
goto :eof

:start_instance
aws ec2 start-instances --instance-ids %1 --region eu-west-2
echo Avviata istanza EC2 con ID: %1
goto :eof