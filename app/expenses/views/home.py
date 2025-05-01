from django.shortcuts import render

def home(request):
    """Home page view showing navigation to different app sections."""
    return render(request, 'expenses/home.html')