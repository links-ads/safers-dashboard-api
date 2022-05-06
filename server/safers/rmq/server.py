#!/usr/bin/python3

# Script to run the RMQ App as a standalone server


def start_rmq():
    from safers.rmq import RMQ
    rmq = RMQ()
    rmq.subscribe()


if __name__ == "__main__":
    import os
    import sys
    import logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

    start_rmq()