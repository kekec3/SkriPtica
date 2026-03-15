from .models import Korisnik


def user_role_processor(request):
    user_id = request.session.get('user_id')
    context = {
        'is_logged_in': False,
        'is_moderator': False,
        'is_admin': False
    }

    if user_id:
        try:
            korisnik = Korisnik.objects.get(pk=user_id)
            context['is_logged_in'] = True
            role = korisnik.idrol.opis.lower()
            if role == 'moderator':
                context['is_moderator'] = True
            elif role == 'admin':
                context['is_moderator'] = True
                context['is_admin'] = True
        except Korisnik.DoesNotExist:
            pass

    return context