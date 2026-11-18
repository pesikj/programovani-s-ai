from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from .case_forms import CaseForm
from .models import Case, Task


@require_safe
def case_list(request):
    query = request.GET.get('q', '').strip()
    cases = Case.objects.select_related('owner').annotate(
        has_open_tasks=Exists(Task.objects.filter(case_id=OuterRef('pk'), completed_at__isnull=True)),
    )
    if query:
        cases = cases.filter(
            Q(title__icontains=query) | Q(company__icontains=query) | Q(questions__icontains=query)
        )
    return render(request, 'crm/case_list.html', {'cases': cases, 'query': query})


@require_safe
def case_detail(request, pk):
    case = get_object_or_404(Case.objects.select_related('owner'), pk=pk)
    tasks = list(case.tasks.select_related('owner').order_by('due_date', 'pk'))
    next_task = next((task for task in tasks if task.completed_at is None), None)
    return render(request, 'crm/case_detail.html', {
        'case': case, 'tasks': tasks, 'next_task': next_task,
        'contacts': case.contacts.all(), 'documents': case.documents.all(),
        'handoffs': case.handoffs.select_related('from_owner', 'to_owner'),
    })


@require_http_methods(['GET', 'POST'])
def case_create(request):
    form = CaseForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        case = form.save()
        return redirect('crm:case-detail', pk=case.pk)
    return render(request, 'crm/case_form.html', {'form': form, 'case': None})


@require_http_methods(['GET', 'POST'])
def case_update(request, pk):
    case = get_object_or_404(Case.objects.select_related('owner'), pk=pk)
    form = CaseForm(request.POST if request.method == 'POST' else None, instance=case)
    if request.method == 'POST' and form.is_valid():
        case = form.save()
        return redirect('crm:case-detail', pk=case.pk)
    return render(request, 'crm/case_form.html', {'form': form, 'case': case})
