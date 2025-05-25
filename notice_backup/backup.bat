@echo off
:: ./notice_backup/backup.bat
:: 复制到备份目录，并重命名为当前日期时间(bcz_notice YY.MM.DD.db)
copy  ..\bcz_notice.db  "..\notice_backup\bcz_notice %date:~2,2%.%date:~5,2%.%date:~8,2%.db"
pause