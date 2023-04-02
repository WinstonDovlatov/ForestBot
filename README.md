# ForestBot

Реализация Телеграмм-бота для определения лесных дорог на космических снимках с применением методов машинного
обучения

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


<img src="readme_images/example_cords_lq.gif" width="414" height="896">

## Реализация 

### Точка входа:
application.py

### Как собрать

1. [Создайте проект Google Cloud](https://console.cloud.google.com/projectcreate)
2. Подключите к нему Google Earth Engine API через API Library
3. Склонируйте репозиторий
4. Скачайте файл [model.onnx](https://drive.google.com/file/d/1TB5jgmAtDGfUffj9J9SUg8K5AZc7prFk/view?usp=sharing) и поместите его в папку "processes"
5. Создайте и заполните файл settings.ini в корневой папке по шаблону [settings_example.ini](https://github.com/WinstonDovlatov/ForestBot/blob/master/settings_example.ini)
5. Собирите образ 

    ```docker build -t bot_image ```
6. Запустите его.

    ```docker run -it --name forest_bot bot_image```
7. В открывшейся консоли необходимо выполнить авторизацию в GoogleCloud в интерактивном режиме. Для этого:
    * Установите GCloud выполнив:
       
        ```./google-cloud-sdk/install.sh```
        
        Со всеми пунктами соглашаемся.
        
    * Авторизуйтесь
    
        ```./google-cloud-sdk/bin/gcloud init```
        
       Здесь потребуется скопировать ссылку полностью(только первая строка будет подсвечиваться) и выполнить авторизацию
       в браузере на вашей машине
       
   * Перезапускаем терминал
   
        ```bash```
   * Выполните авторизацию в Earth Engine
   
        ```earthengine authenticate --quiet```
        
        Вы получите команду, которую необходимо выполнить на вашей машине, на
        которой имеется браузер. Перед вставкой в терминал удалите переносы строк.
        Далее на вашей машине:
        
        * Установите и авторизуйтесь в GCloud, следуя [инструкциям](https://cloud.google.com/sdk/docs/install)
        * Выполните скопированную команду и авторизуйтесь в браузере
        * Скопируйте ссылку, которая появится в терминале. Не забудьте удалить переносы строк
        * Полученную ссылку вставьте в терминал докера
        
   * Запустите бота
   
        ```python application.py```


### Описание структуры проекта

* forest_bot_front - модуль для взаимодействия с Telegram
* osm - модуль для конвертации результатов предсказания в формат .osm
* ml_backend - модуль для обработки полученных изображений с помощью модели
* processes - папка с сторонними процессами, которые используются перед работой
* satellite - модуль для загрузки спутниковых снимков

### TODO

- [x] Docker
- [ ] Ускорить скачивание снимков
- [ ] Переписать используя асинхронную реализацию telebot
- [ ] Перенести код обучения модели в processes
