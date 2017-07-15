from pymongo.errors import AutoReconnect


def autoreconnect_retry(fn, retries=10):
    """decorator for connection retrial"""

    def db_op_wrapper(*args, **kwargs):
        tries = 0
        while tries < retries:
            try:
                return fn(*args, **kwargs)
            except AutoReconnect:
                time.sleep(pow(2, tries))
                tries += 1

        raise Exception("No luck even after %d retries. Start Mongodb \
                            instance" % retries)

    return db_op_wrapper
