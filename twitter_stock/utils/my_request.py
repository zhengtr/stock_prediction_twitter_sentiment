from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from luigi import build
from .wrapper_tasks import LoadAllData
from .analyze_tasks import Predict
from .graph import graph
from .reddit_post import post


@csrf_exempt
def my_page(request):
    """
    Generate initial view of the page.
    """
    context = {}
    context["information"] = (
        "To use this, please click the buttons in the order of LOAD--PREDICT--GRAPH/SHARE. \n "
        "For predictions, please enter date between 2016/05/26 to 2016/06/15. \n "
        "The graph shows the comparison of using/not using our prediction strategy for stock "
        'tradings. \n SHARE will be posting results to subreddit "Prediction". \n '
        "Play around and Enjoy:)"
    )
    context["button1Title"] = "LOAD DATA"
    context["button2Title"] = "PREDICT"
    context["button3Title"] = "GRAPH"

    return render(request, "index.html", context)


@csrf_exempt
def loadingData(request):
    """
    Load data into database.
    """
    build([LoadAllData("all")], local_scheduler=True)
    return HttpResponse()


@csrf_exempt
def predict(request):
    """
    Predict by user's input of ticker and date.
    """
    ticker = request.POST["ticker"]
    myDate = request.POST["myDate"]

    context = {}
    context["information"] = (
        "To use this, please click the buttons in the order of LOAD--PREDICT--GRAPH/SHARE.\n"
        "For predictions, please enter date between 2016/05/26 to 2016/06/15.\n"
        "The graph shows the comparison of using/not using our prediction strategy for stock "
        'tradings.\nSHARE will be posting results to subreddit "Prediction".\n'
        "Play around and Enjoy:)"
    )
    context["button1Title"] = "LOAD DATA"
    context["button2Title"] = "PREDICT"
    context["button3Title"] = "GRAPH"

    if (ticker is None) or (myDate is None):
        return render(request, "", context)

    else:
        ticker = ticker.lower()
        build([Predict(ticker, myDate)], local_scheduler=True)
        myResult = Predict(ticker, myDate).get_result()
        return HttpResponse(myResult)


@csrf_exempt
def mygraph(request):
    """
    Graph of comparisons by user's input on ticker.
    """
    ticker = request.POST["ticker"]

    context = {}
    context["information"] = (
        "To use this, please click the buttons in the order of LOAD--PREDICT--GRAPH/SHARE.\n"
        "For predictions, please enter date between 2016/05/26 to 2016/06/15.\n"
        "The graph shows the comparison of using/not using our prediction strategy for stock "
        'tradings.\nSHARE will be posting results to subreddit "Prediction".\n'
        "Play around and Enjoy:)"
    )
    context["button1Title"] = "LOAD DATA"
    context["button2Title"] = "PREDICT"
    context["button3Title"] = "GRAPH"

    if ticker is None:
        return render(request, "", context)
    else:
        ticker = ticker.lower()
        myDate, nav, nav_strategy = graph(ticker)
        myResult = json.dumps(
            {"date": myDate, "nav": nav, "nav_strategy": nav_strategy}
        )
        return HttpResponse(myResult)


@csrf_exempt
def share(request):
    """
    Share the prediction result by posting to Reddit.
    """
    request.encoding = "utf-8"

    context = {}
    context["information"] = (
        "To use this, please click the buttons in the order of LOAD--PREDICT--GRAPH/SHARE.\n"
        "For predictions, please enter date between 2016/05/26 to 2016/06/15.\n"
        "The graph shows the comparison of using/not using our prediction strategy for stock "
        'tradings.\nSHARE will be posting results to subreddit "Prediction".\n'
        "Play around and Enjoy:)"
    )
    context["button1Title"] = "LOAD DATA"
    context["button2Title"] = "PREDICT"
    context["button3Title"] = "GRAPH"

    ticker = request.POST["ticker"]
    myDate = request.POST["myDate"]

    if (ticker is None) or (myDate is None):
        return render(request, "", context)

    else:
        ticker = ticker.lower()
        myFlag = post(ticker, myDate)
        if myFlag:
            return HttpResponse("Posted to Reddit!")
        else:
            return HttpResponse("Limited! Please try again later!")
