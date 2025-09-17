@echo off
setlocal

rem Check if a commit message was provided
if "%~1"=="" (
    echo.
    echo [31mError: No commit message provided.[0m
    echo.
    echo Usage: PUSH "Your commit message"
    echo.
    goto :end
)

rem Add all changes
echo.
echo [32m--- Adding all changes...[0m
git add .
if %errorlevel% neq 0 (
    echo.
    echo [31mError during git add. Aborting.[0m
    goto :end
)

rem Commit the changes with the provided message
echo.
echo [32m--- Committing changes...[0m
git commit -m "%~1"
if %errorlevel% neq 0 (
    echo.
    echo [31mError during git commit. Aborting.[0m
    goto :end
)

rem Push the changes to the remote repository
echo.
echo [32m--- Pushing to remote repository...[0m
git push
if %errorlevel% neq 0 (
    echo.
    echo [31mError during git push.[0m
    goto :end
)

echo.
echo [32m--- Git operations completed successfully![0m

:end
echo.
endlocal