from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from apps.core.decorators import staff_required
from apps.evacuation.views import evacuation_list_page
import json

from apps.scoping import (
    scoped_evacuation_centers,
    scoped_flood_prone_areas,
    scoped_hazard_zones,
    scoped_infos,
)

User = get_user_model()

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=1)
INVALID_LOGIN_MESSAGE = 'Invalid username or password.'
LOCKED_MESSAGE = 'Too many failed attempts. Locked for 1 minute.'


def service_worker(request):
    """Serve the service worker at the site root so it can control all pages."""
    response = render(request, 'service-worker.js', content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


def _reset_lock_state(request):
    request.session['failed_attempts'] = 0
    request.session['lock_time'] = None


def _get_lock_state(request):
    failed_attempts = request.session.get('failed_attempts', 0)
    lock_time = request.session.get('lock_time')

    if not lock_time:
        return failed_attempts, None

    try:
        unlock_time = timezone.datetime.fromisoformat(lock_time)
    except (TypeError, ValueError):
        _reset_lock_state(request)
        return 0, None

    if timezone.now() < unlock_time:
        remaining = int((unlock_time - timezone.now()).total_seconds())
        return failed_attempts, remaining

    _reset_lock_state(request)
    return 0, None


def _set_lock_state(request):
    lock_until = timezone.now() + LOCK_DURATION
    request.session['failed_attempts'] = MAX_FAILED_ATTEMPTS
    request.session['lock_time'] = lock_until.isoformat()
    return int(LOCK_DURATION.total_seconds())


def _validate_registration_data(data):
    errors = {}

    username = data.get('username', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not username:
        errors['username'] = 'Username is required.'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already taken.'

    if not first_name:
        errors['first_name'] = 'First name is required.'

    if not last_name:
        errors['last_name'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email is required.'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Enter a valid email address.'
        else:
            if User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered.'

    if not password:
        errors['password'] = 'Password is required.'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    else:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors['password'] = ' '.join(exc.messages)

    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    return errors


@require_http_methods(['GET', 'POST'])
def home(request):
    """Public site entry point.

    The main site URL always renders the public live evacuation map and center
    list, for every visitor -- anonymous citizens and logged-in staff creators
    alike. Monitoring views stay available at ``/dashboard/`` for staff.
    """
    return evacuation_list_page(request)


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        # Staff/creators continue to the monitoring dashboard; regular
        # authenticated users (evacuees) are sent to the public map.
        return redirect('dashboard' if request.user.is_staff else 'evacuation:evacuation_list')

    failed_attempts, remaining = _get_lock_state(request)
    if remaining is not None:
        messages.error(request, f'Too many failed attempts. Try again in {remaining} seconds.')
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    if request.method == 'GET':
        return render(request, 'auth/login.html')

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        _reset_lock_state(request)
        login(request, user)
        return redirect('dashboard' if user.is_staff else 'evacuation:evacuation_list')

    failed_attempts += 1
    request.session['failed_attempts'] = failed_attempts
    if failed_attempts >= MAX_FAILED_ATTEMPTS:
        remaining = _set_lock_state(request)
        messages.error(request, LOCKED_MESSAGE)
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    remaining_attempts = MAX_FAILED_ATTEMPTS - failed_attempts
    messages.error(request, f'{INVALID_LOGIN_MESSAGE} {remaining_attempts} attempts remaining.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@staff_required
def dashboard(request):
    """Render the SafeZone overview with KPIs, charts, quick actions and activity."""
    from django.db.models import Sum

    user = request.user
    centers = scoped_evacuation_centers(user)
    infos = scoped_infos(user)

    active_centers = centers.filter(is_active=True, status='available')
    occupancy_totals = active_centers.aggregate(
        sheltered=Sum('current_occupancy'),
        capacity=Sum('capacity'),
    )

    occupied_list = list(
        centers.order_by('name').values('id', 'name', 'current_occupancy', 'capacity', 'status')
    )
    occupancy_data = [
        {
            'name': c['name'],
            'occupied': c['current_occupancy'],
            'remaining': max(0, c['capacity'] - c['current_occupancy']),
            'full': c['status'] != 'available' or c['current_occupancy'] >= c['capacity'],
        }
        for c in occupied_list
    ]

    info_values = list(infos.values('id', 'name', 'age', 'pwd', 'created_at'))
    children = sum(1 for p in info_values if p['age'] <= 12)
    adults = sum(1 for p in info_values if 13 <= p['age'] <= 59)
    seniors = sum(1 for p in info_values if p['age'] >= 60)
    pwds = sum(1 for p in info_values if p['pwd'])

    hazard_zones_count = scoped_hazard_zones(user).count()
    flood_areas_count = scoped_flood_prone_areas(user).count()

    return render(request, 'dashboard.html', {
        'active_centers': active_centers.count(),
        # Evacuees sheltered = total registered evacuee individuals.
        'total_sheltered': infos.count(),
        'total_capacity': occupancy_totals['capacity'] or 0,
        'high_risk_zones': hazard_zones_count + flood_areas_count,
        'occupancy_data': occupancy_data,
        'occupancy_json': json.dumps(occupancy_data),
        'demographics': {
            'children': children,
            'adults': adults,
            'seniors': seniors,
            'pwds': pwds,
        },
        'demographics_json': json.dumps({
            'children': children,
            'adults': adults,
            'seniors': seniors,
            'pwds': pwds,
        }),
        'activities': [
            {
                'id': p['id'],
                'name': p['name'],
                'age': p['age'],
                'created_at': p['created_at'],
            }
            for p in infos.order_by('-created_at').values('id', 'name', 'age', 'created_at')[:8]
        ],
    })


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        # Staff/creators continue to the monitoring dashboard; regular
        # authenticated users (evacuees) are sent to the public map.
        return redirect('dashboard' if request.user.is_staff else 'evacuation:evacuation_list')

    if request.method == 'GET':
        return render(request, 'auth/register.html')

    form_data = {
        'username': request.POST.get('username', ''),
        'first_name': request.POST.get('first_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'email': request.POST.get('email', ''),
        'password': request.POST.get('password', ''),
        'confirm_password': request.POST.get('confirm_password', ''),
    }

    errors = _validate_registration_data(form_data)
    if errors:
        return render(request, 'auth/register.html', {'errors': errors, 'form_data': form_data})

    user = User.objects.create_user(
        username=form_data['username'].strip(),
        first_name=form_data['first_name'].strip(),
        last_name=form_data['last_name'].strip(),
        email=form_data['email'].strip(),
        password=form_data['password'],
    )
    login(request, user)
    # New evacuees land on the public map; they are not system creators.
    return redirect('evacuation:evacuation_list')
