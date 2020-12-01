# Stock Prediction by Twitter Sentiment
[![Build Status](https://travis-ci.com/csci-e-29/2020sp-final-project-jiaxinFL.svg?token=BbqeDYNGsdoASyzAASyJ&branch=master)](https://travis-ci.com/csci-e-29/2020sp-final-project-jiaxinFL)
[![Maintainability](https://api.codeclimate.com/v1/badges/c2ef7cc4b7ab25961579/maintainability)](https://codeclimate.com/repos/5eba15122de8e0016200cbe5/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/c2ef7cc4b7ab25961579/test_coverage)](https://codeclimate.com/repos/5eba15122de8e0016200cbe5/test_coverage)


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
