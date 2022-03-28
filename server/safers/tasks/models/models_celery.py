# just redefining celery-related classes as proxies
# so I can maybe reference them as part of _this_ app
# and group them all together in the django admin

from django_celery_beat.models import (
    ClockedSchedule as CeleryBeatClockedSchedule,
    CrontabSchedule as CeleryBeatCrontabSchedule,
    IntervalSchedule as CeleryBeatIntervalSchedule,
    SolarSchedule as CeleryBeatSolarSchedule,
    PeriodicTask as CeleryBeatPeriodicTask,
    PeriodicTasks as CeleryBeatPeriodicTasks,
)

from django_celery_results.models import (
    TaskResult as CeleryResultsTaskResult,
    ChordCounter as CeleryResultsChordCounter,
    GroupResult as CeleryResultsGroupResult,
)


class ClockedSchedule(CeleryBeatClockedSchedule):
    class Meta:
        proxy = True


class CrontabSchedule(CeleryBeatCrontabSchedule):
    class Meta:
        proxy = True


class IntervalSchedule(CeleryBeatIntervalSchedule):
    class Meta:
        proxy = True


class SolarSchedule(CeleryBeatSolarSchedule):
    class Meta:
        proxy = True


class PeriodicTask(CeleryBeatPeriodicTask):
    class Meta:
        proxy = True


class PeriodicTasks(CeleryBeatPeriodicTasks):
    class Meta:
        proxy = True


class TaskResult(CeleryResultsTaskResult):
    class Meta:
        proxy = True


class ChordCounter(CeleryResultsChordCounter):
    class Meta:
        proxy = True


class GroupResult(CeleryResultsGroupResult):
    class Meta:
        proxy = True