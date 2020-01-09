#!/bin/bash
set -e
wd=$(dirname "$0")
creds=${{full_login}}/${{db_password}}

if [[ -z "$1" ]] 
then
    echo "Password required for new {database_user} user."
    exit 1
fi

echo "Creating {database_user} user..."
echo 'quit;' | sqlplus ${{creds}} @${{wd}}/{database_user}.ddl.sql ${{1}}
echo "{database_user} created."

# add additional setup stuff here

echo "{database_user} initialization completed."