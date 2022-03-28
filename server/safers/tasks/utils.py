import fnmatch

from celery.exceptions import NotRegistered, CeleryError

from safers.tasks.celery import app as celery_app

# def get_all_tasks():
#     tasks = [
#         task for task_name,
#         task in sorted(celery_app.tasks.items())
#         if not task_name.startswith("celery")
#     ]
#     return tasks


def get_task(task_name, pattern_match=True):
    """
    gets a task either by exact name or by fnmatch-style matching
    """
    tasks = celery_app.tasks
    if pattern_match:
        matching_tasks = fnmatch.filter(tasks.keys(), task_name)
        if len(matching_tasks) == 1:
            return tasks[matching_tasks[0]]
        elif len(matching_tasks) > 1:
            raise CeleryError("multiple tasks matched pattern")
    else:
        try:
            return tasks[task_name]
        except NotRegistered:
            pass
