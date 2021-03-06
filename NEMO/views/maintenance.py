from itertools import chain

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET

from NEMO.models import Task, TaskCategory


@staff_member_required(login_url=None)
@require_GET
def maintenance(request, sort_by=''):
	pending = Q(status=Task.Status.REQUIRES_ATTENTION) | Q(status=Task.Status.WORK_IN_PROGRESS)
	pending_tasks = Task.objects.filter(pending)
	if sort_by in ['urgency', 'force_shutdown', 'tool', 'problem_category', 'last_updated', 'creation_time']:
		if sort_by == 'last_updated':
			pending_tasks = pending_tasks.exclude(last_updated=None).order_by('-last_updated')
			not_yet_updated_tasks = Task.objects.filter(pending, last_updated=None).order_by('-creation_time')
			pending_tasks = list(chain(pending_tasks, not_yet_updated_tasks))
		else:
			pending_tasks = pending_tasks.order_by(sort_by)
			if sort_by in ['urgency', 'force_shutdown', 'creation_time']:
				pending_tasks = pending_tasks.reverse()
	else:
		pending_tasks = pending_tasks.order_by('urgency').reverse()  # Order by urgency by default
	closed = Q(status=Task.Status.COMPLETE) | Q(status=Task.Status.CANCELLED)
	closed_tasks = Task.objects.filter(closed).exclude(resolution_time__isnull=True).order_by('-resolution_time')[:20]
	dictionary = {
		'pending_tasks': pending_tasks,
		'closed_tasks': closed_tasks,
	}
	return render(request, 'maintenance/maintenance.html', dictionary)


@staff_member_required(login_url=None)
@require_GET
def task_details(request, task_id):
	task = get_object_or_404(Task, id=task_id)

	if task.status in [task.Status.COMPLETE, task.Status.CANCELLED]:
		return render(request, 'maintenance/closed_task_details.html', {'task': task})

	dictionary = {
		'task': task,
		'initial_assessment_categories': TaskCategory.objects.filter(stage=TaskCategory.Stage.INITIAL_ASSESSMENT),
		'completion_categories': TaskCategory.objects.filter(stage=TaskCategory.Stage.COMPLETION),
	}

	if task.tool.is_configurable():
		dictionary['rendered_configuration_html'] = task.tool.configuration_widget(request.user)

	return render(request, 'maintenance/pending_task_details.html', dictionary)
