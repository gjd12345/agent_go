@echo off
cd /d C:\Users\24294\.trae\Archive_2\Archive_0422
echo [%date% %time%] Starting EOH flash grid experiment...
python _run_eoh_grid.py
echo [%date% %time%] DONE
pause
