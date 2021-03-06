from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from NEMO.models import Reservation, UsageEvent, Alert, Resource, LandingPageChoice
from NEMO.views.alerts import delete_expired_alerts


@login_required
@require_GET
def landing(request):
	delete_expired_alerts()
	usage_events = UsageEvent.objects.filter(operator=request.user.id, end=None).prefetch_related('tool', 'project')
	tools_in_use = [u.tool_id for u in usage_events]
	fifteen_minutes_from_now = timezone.now() + timedelta(minutes=15)
	dictionary = {
		'now': timezone.now(),
		'alerts': Alert.objects.filter(Q(user=None) | Q(user=request.user), debut_time__lte=timezone.now()),
		'usage_events': usage_events,
		'upcoming_reservations': Reservation.objects.filter(user=request.user.id, end__gt=timezone.now(), cancelled=False, missed=False, shortened=False).exclude(tool_id__in=tools_in_use, start__lte=fifteen_minutes_from_now).order_by('start')[:3],
		'disabled_resources': Resource.objects.filter(available=False),
		'landing_page_choices': LandingPageChoice.objects.all(),
	}
	return render(request, 'landing.html', dictionary)
