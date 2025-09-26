@echo off
setlocal enabledelayedexpansion

REM ====== CONFIGURATION ======
set REMOTE_HOST=dpg-d2u4krje5dus73edak2g-a.virginia-postgres.render.com
set REMOTE_DB=iccl_league_db
set REMOTE_USER=root
set REMOTE_PASS=2QboXNFrGcjj3kdl3ZsymdV3q6PpwzjY

set LOCAL_HOST=localhost
set LOCAL_DB=iccl_league_db
set LOCAL_USER=root
set LOCAL_PASS=psra10051986

REM ====== TABLE LIST (comma-separated for TRUNCATE) ======
set TABLES_TRUNC=league_card, league_goal, league_match, league_player, league_sponsor, league_team, league_team_standing, league_teamoftheweek, league_tournament

REM ====== STEP 1: TRUNCATE LOCAL TABLES ======
echo 🔹 Truncating local tables (you will be prompted for local password)...
psql -h %LOCAL_HOST% -U %LOCAL_USER% -d %LOCAL_DB% -c "TRUNCATE TABLE %TABLES_TRUNC% RESTART IDENTITY CASCADE;"

echo Using user: %LOCAL_USER% with DB: %LOCAL_DB%
REM ====== STEP 2: COPY DATA FROM REMOTE TO LOCAL ======
echo 🔹 Dumping remote data (you will be prompted for remote password)...
pg_dump -h %REMOTE_HOST% -U %REMOTE_USER% -d %REMOTE_DB% --data-only --disable-triggers -t league_card -t league_goal -t league_match -t league_player -t league_sponsor -t league_team -t league_team_standing -t league_teamoftheweek -t league_tournament | psql -h %LOCAL_HOST% -U %LOCAL_USER% -d %LOCAL_DB%

echo ✅ Local database has been refreshed from remote!

endlocal
pause