from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'index.html')

def catalog(request):
    return render(request, 'catalog.html')

def card(request):
    return render(request, 'card.html')

def consultation(request):
    return render(request, 'consultation.html')

def order(request):
    return render(request, 'order.html')

def order_step(request):
    return render(request, 'order-step.html')

def order_complete(request):
    # Здесь будет логика обработки заказа
    return render(request, 'order-step.html')

def quiz(request):
    return render(request, 'quiz.html')

def quiz_step(request):
    return render(request, 'quiz-step.html')

def result(request):
    return render(request, 'result.html')

def privacy(request):
    # Создайте шаблон privacy.html или перенаправляйте куда-то
    return render(request, 'privacy.html')
