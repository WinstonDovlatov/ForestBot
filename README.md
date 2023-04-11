# ForestBot

Реализация Телеграмм-бота для определения лесных дорог на космических снимках с применением методов машинного
обучения.

## Пользовательская часть

### Ключевые особенности

* Получение снимка по координатам и поиск на нем лесных дорог 
    * В текстовом виде
    * С помощью отправки геопозиции(мобильная версия)
* Ковертация полученных результатов в формат хранение географических объектов(OSM)
* Поиск дорог на отправленной пользователем фотографии


### Дополнительные возможности

* Возможность отмены поиска дорог при получении снимка по координатам
* Изменение чувствительности модели с помощью команды /set_sensitivity {value}
* Изменение радиуса(в км) снимка с помощью команды /set_radius {value} 
* Получение приветственного руководства /start
* Получение исчерпывающего руководства /help

### Примеры

Отправьте координаты, а бот пришлет космический снимок, 
а затем и найдет на нем дороги!


<img src="readme_images/example_cords_lq.gif" width="330" height="716">

## Реализация 

### Точка входа:
[entrypoint.py](https://github.com/WinstonDovlatov/ForestBot/blob/master/entrypoint.py)

### Как собрать

#### I. Регистрация в Google Cloud

1. [Создайте проект Google Cloud](https://console.cloud.google.com/projectcreate)
2. Подключите к нему Google Earth Engine API через API Library

#### II. Создание бота в Telegram

1. Зарегистрируйте вашего бота с помощью [BotFather](https://telegram.me/BotFather) 
2. Сохраните полученный токен. Он пригодится далее в следующем шаге при генерации реквизитов

#### III. Ручная сборка контейнера

1. Склонируйте репозиторий
   
   ```$ git clone https://github.com/WinstonDovlatov/ForestBot.git```
   
   и перейдите к корневую папку
   
   ``` $ cd forestbot ```

2. Скачайте модель [model.onnx](https://drive.google.com/file/d/1TB5jgmAtDGfUffj9J9SUg8K5AZc7prFk/view?usp=sharing) и поместите ее в папку ["forestbot/processes"](https://github.com/WinstonDovlatov/ForestBot/tree/master/forestbot/processes)
3. Создайте и заполните файл с реквизитами credentials.ini в корневой папке по шаблону [credentials_example.ini](https://github.com/WinstonDovlatov/ForestBot/blob/master/credentials_example.ini)
или с помощью команды:
    
    ```$ python generate_credentials <YOUR_TELEGRAM_TOKEN> <YOUR_G-CLOUD_PROJECT_NAME>```
4. Собирите образ 

    ```$ docker build -t bot_image .```
    
5. Запустите его

    ```$ docker run -it --name forest_bot bot_image```
    
#### *III. Альтернативно: скачать готовый образ

1. Скачайте [образ](https://github.com/WinstonDovlatov/ForestBot/pkgs/container/forestbot)

    ```$ docker pull ghcr.io/winstondovlatov/forestbot:latest```
    
2. Запустите контейнер

    ```$ docker run -it --name forest_bot winstondovlatov/forestbot```
    
3. Внутри докера необходимо сгенирировать реквизиты

    ```$ python generate_credentials.py <YOUR_TELEGRAM_TOKEN> <YOUR_G-CLOUD_PROJECT_NAME>```
     
#### IV. Автоизация в GoogleCloud и запуск бота
В открывшейся консоли контейнера необходимо выполнить авторизацию в GoogleCloud в интерактивном режиме. 
Для этого:

1. Установите GCloud выполнив:
   
    ```$ ./google-cloud-sdk/install.sh```
    
    Со всеми пунктами соглашаемся. Путь оставляем пустным
    
2. Авторизуйтесь

    ```$ ./google-cloud-sdk/bin/gcloud init```
    
   Здесь потребуется скопировать ссылку полностью и выполнить авторизацию
   в браузере на вашей машине. Полученный код вставить в терминал
   
3. Перезапускаем терминал
   
    ```$ bash```
4. Выполните авторизацию в Earth Engine

    ```$ earthengine authenticate --quiet```

    Вы получите команду, которую необходимо выполнить на вашей машине, на
    которой имеется браузер. Перед вставкой в терминал удалите переносы строк.
    Далее на вашей машине:

    * Установите и авторизуйтесь в GCloud, следуя [инструкциям](https://cloud.google.com/sdk/docs/install)
    * Выполните скопированную команду и авторизуйтесь в браузере
    * Скопируйте ссылку, которая появится в терминале. Не забудьте удалить переносы строк
    * Полученную ссылку вставьте в терминал докер-контейнера
        
5. Запустите бота

    ```$ python entrypoint.py```

### TODO

- [x] Docker
- [ ] Ускорить скачивание снимков
- [ ] Переписать используя асинхронную реализацию telebot
- [ ] Перенести код обучения модели в processes
