import csv
import io

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q

from apps.scoping import (
    scoped_evacuation_center,
    scoped_evacuation_centers,
    scoped_flood_prone_areas,
    scoped_hazard_zones,
    scoped_infos,
)
from apps.core.decorators import staff_required
from apps.info.models import Info
from .models import EvacuationCenter

VALID_STATUSES = [choice[0] for choice in EvacuationCenter.STATUS_CHOICES]

# Safe, transparency-friendly label for a shelter record that performed a check-in.
CHECKED_IN_STATUS = 'Checked In'


def _parse_int(raw_value):
    """Convert a value to a non-negative integer, returning None when invalid."""
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _parse_float(raw_value):
    """Convert a value to a float, returning None when invalid."""
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


@require_http_methods(['GET', 'POST'])
def evacuation_list_page(request):
    """Render the searchable, paginated evacuation center list.

    PUBLIC VIEW: no authentication required. Citizens, residents and evacuees
    can instantly browse live evacuation centers, capacities and statuses.
    """
    query = request.GET.get('q', '').strip()

    centers_list = scoped_evacuation_centers(request.user).order_by('name')

    if query:
        centers_list = centers_list.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(contact_person__icontains=query)
        )

    paginator = Paginator(centers_list, 10)
    page_number = request.GET.get('page', 1)
    centers = paginator.get_page(page_number)

    return render(request, 'evacuation.html', {
        'centers': centers,
        'query': query,
        'status_choices': EvacuationCenter.STATUS_CHOICES,
        'hazard_zones': scoped_hazard_zones(request.user).order_by('name'),
        'flood_prone_areas': scoped_flood_prone_areas(request.user).order_by('name'),
    })


@require_http_methods(['GET', 'POST'])
def evacuation_list_ajax(request):
    """Return the filtered evacuation centers as paginated JSON.

    PUBLIC VIEW: safe to call without an authenticated session because it only
    exposes operational capacity/status data.
    """
    query = request.GET.get('q', '').strip()

    centers_list = scoped_evacuation_centers(request.user).order_by('name')

    if query:
        centers_list = centers_list.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(contact_person__icontains=query)
        )

    paginator = Paginator(centers_list, 10)
    page_number = request.GET.get('page', 1)
    centers = paginator.get_page(page_number)
    data = list(centers.object_list.values(
        'id', 'name', 'capacity', 'current_occupancy',
        'status', 'supplies',
    ))
    return JsonResponse({
        'data': data,
        'has_next': centers.has_next(),
        'has_prev': centers.has_previous(),
        'page': centers.number,
        'pages': centers.paginator.num_pages,
        'total': centers.paginator.count,
    })


@require_http_methods(['GET', 'POST'])
def evacuation_get_ajax(request, pk):
    """Return one evacuation center as JSON.

    PUBLIC VIEW: read-only operational data used by the public map, search and
    route-planning features. Only transparency-safe fields are returned: the
    exact address and contact numbers stay visible to staff only and are never
    exposed through this public endpoint.
    """
    center = scoped_evacuation_center(request.user, pk)
    return JsonResponse({
        'id': center.id,
        'name': center.name,
        'latitude': center.latitude,
        'longitude': center.longitude,
        'capacity': center.capacity,
        'current_occupancy': center.current_occupancy,
        'status': center.status,
        'supplies': center.supplies,
    })


@require_http_methods(['GET'])
def public_evacuee_list(request, center_id):
    """Render the safe check-in list for one evacuation center.

    PUBLIC VIEW: no authentication required. Family members, local community
    and citizens may open this page without a login to see who has safely
    checked in to a given evacuation center and when.

    Only transparency-safe fields cross the privacy boundary:

    - evacuee name / alias
    - evacuation center name
    - check-in status (e.g. "Checked In")
    - date / time of the check-in

    Sensitive personal details (contact numbers, exact addresses, medical
    records, ages, e-mail addresses, ...) are deliberately never loaded or
    rendered here.

    Evacuees are matched through ``Info.evacuation_center`` (a real foreign
    key), so each center only ever shows the people actually checked in to
    *that* center -- even when several centers share the same creator.

    The optional ``center`` GET parameter lets the public live-search box
    switch the list to another evacuation center than the one encoded in the
    URL.
    """
    center = get_object_or_404(EvacuationCenter, pk=center_id)

    query = request.GET.get('q', '').strip()

    selected_center = center
    selected_center_id = request.GET.get('center', '').strip()
    if selected_center_id.isdigit():
        selected_center = get_object_or_404(EvacuationCenter, pk=int(selected_center_id))

    evacuees = (
        Info.objects.filter(evacuation_center=selected_center)
        .select_related('evacuation_center')
        .order_by('name')
    )

    if query:
        evacuees = evacuees.filter(name__icontains=query)

    evacuee_records = [
        {
            'id': info.pk,
            'name': info.name,
            'center': selected_center.name,
            'check_in': info.created_at,
            'status': CHECKED_IN_STATUS,
        }
        for info in evacuees
    ]

    return render(request, 'public_evacuees.html', {
        'center': selected_center,
        'evacuees': evacuee_records,
        'query': query,
        'centers': scoped_evacuation_centers(request.user).order_by('name'),
    })


@require_http_methods(['GET'])
def public_evacuee_search_ajax(request):
    """Return safe evacuee check-in matches for live (client-side) search.

    PUBLIC VIEW: no authentication required. Used by the public "View Evacuees"
    experience so family members can search across evacuation centers by name
    without a full page round-trip.

    Two search modes are supported through the ``center_id`` GET parameter:

    - no ``center_id``  -> search across all evacuation centers (family member
      may be sheltered under any center);
    - ``center_id``      -> restrict the search to a single evacuation center.

    Matching is done on ``Info.evacuation_center`` so a center's results never
    include people registered at another center by the same creator.

    Only transparency-safe fields (name, check-in time, status) are returned;
    personal details never leave the database through this endpoint.
    """
    query = request.GET.get('q', '').strip()
    center_id = request.GET.get('center_id', '').strip()

    centers = scoped_evacuation_centers(request.user)
    if center_id.isdigit():
        centers = centers.filter(pk=int(center_id))

    evacuees = (
        Info.objects.filter(evacuation_center__in=centers)
        .select_related('evacuation_center')
        .order_by('name')
    )

    if query:
        evacuees = evacuees.filter(name__icontains=query)

    total = evacuees.count()

    results = [
        {
            'id': info.pk,
            'name': info.name,
            'center': info.evacuation_center.name if info.evacuation_center_id else '',
            'check_in': info.created_at,
            'status': CHECKED_IN_STATUS,
        }
        for info in evacuees[:100]
    ]

    return JsonResponse({
        'query': query,
        'results': results,
        'total': total,
    })


@staff_required
@require_http_methods(['GET'])
def evacuee_report_csv(request):
    """Return the full checked-in evacuees report as a CSV file download.

    CREATOR / ADMIN ONLY: downloading full reports (which include personal
    attributes such as age or family head) is strictly reserved for
    authenticated staff (creators / administrators) of the system. Anonymous
    visitors are redirected to the login page and authenticated non-staff users
    receive a 403 Forbidden.
    """
    infos = scoped_infos(request.user).select_related('evacuation_center').order_by('name')

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Evacuee Name',
        'Age',
        'Evacuation Center',
        'Family Head',
        'Check-In Time',
        'Status',
    ])

    for info in infos:
        center_name = info.evacuation_center.name if info.evacuation_center_id else ''
        writer.writerow([
            info.name,
            info.age,
            center_name,
            info.family_head or '',
            info.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            CHECKED_IN_STATUS,
        ])

    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="safezone_evacuees.csv"'
    return response


@staff_required
@require_POST
def evacuation_save_ajax(request):
    """Validate and create or update an evacuation center, returning its data as JSON.

    CREATOR / ADMIN ONLY: adding or editing evacuation centers requires a
    staff (creator) session.
    """
    center_id = request.POST.get('id')

    if center_id:
        center = scoped_evacuation_center(request.user, center_id)
        is_update = True
    else:
        center = EvacuationCenter()
        is_update = False

    name = request.POST.get('name', '').strip()
    address = request.POST.get('address', '').strip()
    capacity_raw = request.POST.get('capacity', '').strip()
    occupancy_raw = request.POST.get('current_occupancy', '').strip()
    status = request.POST.get('status', '').strip()
    contact_person = request.POST.get('contact_person', '').strip()
    contact_number = request.POST.get('contact_number', '').strip()
    supplies = request.POST.get('supplies', '').strip()
    latitude_raw = request.POST.get('latitude', '').strip()
    longitude_raw = request.POST.get('longitude', '').strip()

    if not latitude_raw or not longitude_raw:
        return JsonResponse({'error': 'Latitude and longitude are required.'}, status=400)

    latitude = _parse_float(latitude_raw)
    longitude = _parse_float(longitude_raw)

    if latitude is None:
        return JsonResponse({'error': 'Latitude must be a number.'}, status=400)

    if longitude is None:
        return JsonResponse({'error': 'Longitude must be a number.'}, status=400)

    if not -90 <= latitude <= 90:
        return JsonResponse({'error': 'Latitude must be between -90 and 90.'}, status=400)

    if not -180 <= longitude <= 180:
        return JsonResponse({'error': 'Longitude must be between -180 and 180.'}, status=400)

    if not name:
        return JsonResponse({'error': 'Name is required.'}, status=400)

    if not address:
        return JsonResponse({'error': 'Address is required.'}, status=400)

    capacity = _parse_int(capacity_raw)
    if capacity is None or capacity < 1:
        return JsonResponse({'error': 'Capacity must be a number of at least 1.'}, status=400)

    occupancy = _parse_int(occupancy_raw)
    if occupancy is None:
        return JsonResponse({'error': 'Current occupancy must be a non-negative number.'}, status=400)

    if occupancy > capacity:
        return JsonResponse({'error': 'Current occupancy cannot exceed capacity.'}, status=400)

    if status not in VALID_STATUSES:
        return JsonResponse({'error': 'Select a valid status.'}, status=400)

    center.name = name
    center.address = address
    center.capacity = capacity
    center.current_occupancy = occupancy
    center.status = status
    center.contact_person = contact_person
    center.contact_number = contact_number
    center.supplies = supplies
    center.latitude = latitude
    center.longitude = longitude

    if not center.pk:
        center.user = request.user

    try:
        center.save()
    except IntegrityError:
        return JsonResponse(
            {'error': 'Could not save record due to a conflict.'},
            status=400
        )

    messages.success(
        request,
        f'Evacuation center "{center.name}" has been {"updated" if is_update else "saved"} successfully.'
    )

    return JsonResponse({
        'status': 'success',
        'id': center.id,
        'name': center.name,
        'address': center.address,
        'latitude': center.latitude,
        'longitude': center.longitude,
        'capacity': center.capacity,
        'current_occupancy': center.current_occupancy,
        'status': center.status,
        'contact_person': center.contact_person,
        'contact_number': center.contact_number,
        'supplies': center.supplies,
    })


@staff_required
@require_POST
def evacuation_delete_ajax(request, pk):
    """Delete the specified evacuation center and confirm as JSON.

    CREATOR / ADMIN ONLY: deleting evacuation centers requires a staff
    (creator) session.
    """
    center = scoped_evacuation_center(request.user, pk)
    center_name = center.name
    center.delete()
    messages.success(request, f'Evacuation center "{center_name}" has been deleted successfully.')
    return JsonResponse({'status': 'deleted'})
