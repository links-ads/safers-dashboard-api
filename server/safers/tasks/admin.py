from django.contrib import admin

from django_celery_beat.admin import (
    ClockedScheduleAdmin as CeleryBeatClockedScheduleAdmin,
    PeriodicTaskAdmin as CeleryBeatPeriodicTaskAdmin,
)
from django_celery_beat.models import (
    IntervalSchedule as CeleryBeatIntervalSchedule,
    CrontabSchedule as CeleryBeatCrontabSchedule,
    SolarSchedule as CeleryBeatSolarSchedule,
    ClockedSchedule as CeleryBeatClockedSchedule,
    PeriodicTask as CeleryBeatPeriodicTask,
)

from django_celery_results.admin import (
    TaskResultAdmin as CeleryResultsTaskResultAdmin,
    GroupResultAdmin as CeleryResultsGroupResultAdmin,
)
from django_celery_results.models import (
    TaskResult as CeleryResultsTaskResult,
    GroupResult as CeleryResultsGroupResult,
)

from safers.tasks.models import (
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
    PeriodicTask,
    TaskResult,
    GroupResult,
)

# TODO: SOMETHING'S GOING WRONG W/ CeleryResultsTaskResultAdmin ?
for model in (
    CeleryBeatIntervalSchedule,
    CeleryBeatCrontabSchedule,
    CeleryBeatSolarSchedule,
    CeleryBeatClockedSchedule,
    CeleryBeatPeriodicTask,
    CeleryResultsTaskResult,
    CeleryResultsGroupResult,
):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

admin.site.register(IntervalSchedule)
admin.site.register(CrontabSchedule)
admin.site.register(SolarSchedule)
admin.site.register(ClockedSchedule, CeleryBeatClockedScheduleAdmin)
admin.site.register(PeriodicTask, CeleryBeatPeriodicTaskAdmin)
admin.site.register(TaskResult, CeleryResultsTaskResultAdmin)
admin.site.register(GroupResult, CeleryResultsGroupResultAdmin)
