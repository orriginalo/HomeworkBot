# Определение списка исключаемых файлов и каталогов
$excludeList = @('.venv', '.vscode', '__pycache__', '.env', '/data')

# Создание массива параметров --exclude для каждого элемента
$excludeArgs = $excludeList | ForEach-Object { "--exclude=$_" }

# Запрос у пользователя, нужно ли удалить файлы на сервере перед переносом
$deleteChoice = Read-Host "Удалить файлы на сервере перед переносом? (y/n)"

# Если пользователь выбрал 'y', удаляем файлы на сервере
if ($deleteChoice -eq 'y') {
    Write-Host "Удаление файлов на сервере..."
    ssh orriginalo@10.242.106.91 "sudo -S rm -rf /home/orriginalo/docker/HomeworkBotTesting/*"
}

# Команда rsync с передачей каждого исключения отдельным параметром
Write-Host "Перенос файлов на сервер..."
wsl rsync -avz --no-times $excludeArgs ./ orriginalo@10.242.106.91:/home/orriginalo/docker/HomeworkBotTesting/