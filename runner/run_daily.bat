@echo off
rem 续火花每日运行外壳：先无头跑，退出码 >= 2 时退回有头跑一次。
rem 定时任务只需指向本文件，无需在这里写任何个人路径。
setlocal
set HERE=%~dp0
if "%PYTHON_BIN%"=="" set PYTHON_BIN=python
set CFG=%HERE%..\config\runner.json

"%PYTHON_BIN%" "%HERE%douyin_spark_daily.py" --config "%CFG%"
set RC=%ERRORLEVEL%
if %RC% GEQ 2 (
  "%PYTHON_BIN%" "%HERE%douyin_spark_daily.py" --config "%CFG%" --headed
)
endlocal
