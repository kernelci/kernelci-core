import celery.result
import taskqueue.celery as taskc
import utils


@taskc.app.task(name="error-handler")
def error_handler(uuid):
    # ToDo: propagate error if the HTTP response hasn't been sent already
    with celery.result.allow_join_result():
        result = celery.result.AsyncResult(uuid)
        ex = result.get(propagate=False)
        utils.LOG.error("Task failed, UUID: {}, error: {}".format(uuid, ex))
