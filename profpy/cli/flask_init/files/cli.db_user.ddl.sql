DECLARE
    userexists integer;
BEGIN
    SELECT CAST(COUNT(*) AS INTEGER) INTO userexists FROM dba_users WHERE username='{database_user}';
    if (userexists = 0) then
        execute immediate 'CREATE USER {database_user} IDENTIFIED BY &&1 DEFAULT TABLESPACE USERS account unlock PROFILE NO_PWD_EXPIRY';
    end if;

end;
/
grant connect to {database_user};
grant create table to {database_user};
grant unlimited tablespace to {database_user};
grant resource to {database_user};
grant create session to {database_user};
grant create type to {database_user};
{additional_grants}
show errors;