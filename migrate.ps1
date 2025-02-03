# Конфигурация
$LocalDBContainer = "homeworkbot-db-1"
$ServerUser = "orriginalo"
$ServerIP = "10.242.106.91"
$ServerDBContainer = "homeworkbot-db-1"
$BackupFile = "domashkabot_backup.dump"
$PGPassword = "domashkabot"  # Ваш пароль от БД

# 1. Создать дамп в локальном контейнере
Write-Host "Создание бэкапа..."
docker exec $LocalDBContainer pg_dump `
    -h localhost -p 5432 -U domashkabot -d domashkabot -Fc -f $BackupFile

# 2. Скопировать файл из контейнера на хост
Write-Host "Копирование файла с контейнера..."
docker cp "${LocalDBContainer}:/${BackupFile}" .

# 3. Перенести файл на сервер
Write-Host "Копирование на сервер..."
scp "./${BackupFile}" "${ServerUser}@${ServerIP}:~/${BackupFile}"

# 4-5. Восстановить дамп на сервере
Write-Host "Восстановление бэкапа..."
$RemoteCommands = @"

docker cp ~/$BackupFile ${ServerDBContainer}:/$BackupFile
docker exec ${ServerDBContainer} bash -c "PGPASSWORD='${PGPassword}' pg_restore -h db -p 5432 -U domashkabot -d domashkabot -v /$BackupFile"
rm ~/$BackupFile
"@
ssh ${ServerUser}@${ServerIP} $RemoteCommands

# Очистка
Remove-Item "./${BackupFile}"
Write-Host "Готово!"