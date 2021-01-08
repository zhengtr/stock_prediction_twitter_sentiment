# Stock Prediction by Twitter Sentiment


## Description

Studies and reports have shown that how people tweet is related to stock market values. Generally, Positive sentiment indicated positive change in stock values. In this project, I built a model that analyzes Twitter sentiment, and use it to predict buy/sell signals for stocks. The users can use Django web interface to check on each stock and get predictions for buy/sell.


## Usage

```
pipenv run python manage.py runserver --nothreading --noreload
```
Note: Luigi has threading issues when building from Django. Use `--nothreading` is a workaround for getting the server running and luigi task properly building.


## Tools Used


| Tools         |Explanation            |
| :-------------|:----------------------|
|**Luigi**      |created *SQLiteBaseTarget*; make use of *WrapperTask*; class inheritance|
|**SQLAlchemy** |tried *SQLALchemy* to compare with Django ORM as we used in previous pset|
|**MVC**        |tried direct implementation of MCV to compare with Django's as we used in previous pset|
|**Dask**       |used `@delayed` to help with methods that Dask does not support|
|**html**       |probably out of scope, but tried it for better presentation of website|
|**Decorators** |`@delayed`, `@csrf_exempt`|
|**API**        |Reddit *API* to post content|


## Snapshots of the Website
![Alt text](screen_shot.jpg?raw=true "Screen Shot")
