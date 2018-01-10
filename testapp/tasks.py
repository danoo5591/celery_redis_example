from celery import task, shared_task, current_task
from celery.five import monotonic
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger

from numpy import random
from scipy.fftpack import fft
##############################################
from contextlib import contextmanager
from django.core.cache import cache
from hashlib import md5
##############################################

logger = get_task_logger(__name__)

def sum(x,y):
    import time
    animation = "|/-\\"
    idx = 0
    flag = True
    cant = 10
    while flag:
        if idx < cant:
            a = 0
            # print animation[idx % len(animation)] + "\r",
        else:
            a = 1
            # print " " + "\r",
            flag = False
        time.sleep(0.2)
        idx += 1
    return x+y


LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes

@contextmanager
def memcache_lock(lock_id, value):
    timeout_at = monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, value, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if monotonic() < timeout_at:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else.
            cache.delete(lock_id)


@shared_task
def fft_random(n):
    """
    Brainless number crunching just to have a substantial task:
    """
    for i in range(n):
        x = random.normal(0, 0.1, 2000)
        y = fft(x)
        if(i%30 == 0):
            process_percent = int(100 * float(i) / float(n))
            current_task.update_state(state='PROGRESS',
                                      meta={'process_percent': process_percent})
    return random.random()


@shared_task
def add(x,y):
    return sum(x,y)


@task()
def sum_task():
    x = random.randint(0,100)
    y = random.randint(0,100)
    s = sum(x,y)
    logger.info("[sum_task]: %s + %s = %s" % (x,y,s))
    return s

# @periodic_task(run_every=(crontab(minute='*/15')),name="sum_task",ignore_result=True)
# A periodic task that will run every minute (the symbol "*" means every)
# @periodic_task(run_every=(crontab(hour="*", minute="*", day_of_week="*")))
@task(bind=True)
def random_sum(self):
    """
    Periodic task example
    """
    import random
    CANT_TUPLES = 50
    MIN = 0
    MAX = 100
    # lock_id = '{0}-lock-{1}'.format(self.name, 'semaphore')
    lock_id = 'lock'
    logger.info('Importing random_sum: %s %s' % (lock_id, self.app.oid))
    with memcache_lock(lock_id, 'semaphore') as acquired:
        logger.info("acquired?: "+str(acquired))
        if acquired:
            random.seed()
            random_tuple_list = [(random.randint(MIN,MAX),random.randint(MIN,MAX)) for i in range(CANT_TUPLES)]
            for i,(x,y) in enumerate(random_tuple_list):
                s = sum(x,y)
                logger.info("[Index %s]: %s + %s = %s" % (i,x,y,s))
    logger.info('random_sum is already being imported by another worker')