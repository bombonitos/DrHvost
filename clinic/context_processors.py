from .models import Vet

def is_vet(request):
    """
    Добавляет в контекст шаблона информацию о том, является ли пользователь врачом
    """
    if request.user.is_authenticated:
        is_vet = Vet.objects.filter(user=request.user).exists()
        return {'is_vet': is_vet}
    return {'is_vet': False} 