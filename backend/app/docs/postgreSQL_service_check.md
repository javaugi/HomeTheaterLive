Most command uses PowerShell as an example

1. Windows default data location
    C:\Program Files\PostgreSQL\<version>\data
    or
    C:\ProgramData\PostgreSQL\<version>\data
    or cutomized location (especially for upgrade)
    C:\pgdata\18
2. The data structures look like the following: (that is a PostgreSQL cluster)
    base
    global
    pg_wal
    pg_multixact
    PG_VERSION
3. services.msc to see
    postgresql-x64-17
    postgresql-x64-18

    right click to see the startup data path
"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" runservice -N "postgresql-x64-18" -D "C:\Program Files\PostgreSQL\18\data" -w

4. Proper upgrade use
    pg_upgrade

    Typical steps:
        1. Stop both services
            sudo net stop postgresql-x64-18
        2. backup by running:  pg_dumpall > backup.sql
        3. Run pg_upgrade using old and new bin directories
        4. Start new service
            sudo net start postgresql-x64-18

5. Switch data directory
    1. start the service postgresql-x64-18 from services.msc console or net stop postgresql-x64-18 from powershell
    2. sudo sc delete postgresql-x64-18  from powershell
    3. Step 3 — Recreate the service pointing to C:\pgdata\18

Run cmd as admin:
"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" register -N "postgresql-x64-18" -D "C:\pgdata\18" -U "postgres" -S auto

 or multiline

"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" register ^
-N "postgresql-x64-18" ^
-D "C:\pgdata\18" ^
-U "postgres" ^
-S auto

or run Powershell as admin

& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" register -N "postgresql-x64-18" -D "C:\pgdata\18" -U "postgres" -S auto


    4. net start postgresql-x64-18 from powershell
    5. verify frm postgreSQL admin psql console
        psql -U postgres

    6. Quick but less clean: Edit service ImagePath by running regedit
    You can modify:
        HKLM\SYSTEM\CurrentControlSet\Services\postgresql-x64-18
        Computer\HKEY_CURRENT_CONFIG\System\CurrentControlSet\Services\postgresql-x64-18
    Change:
        -D "C:\Program Files\PostgreSQL\18\data"
    to:
        -D "C:\pgdata\18"