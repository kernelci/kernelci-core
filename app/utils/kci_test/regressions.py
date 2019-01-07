# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Logic to find regressions in test group results."""

import bson
import redis

import models
import models.test_regression
import utils
import utils.db
import utils.database.redisdb as redisdb

REGRESSION_SPEC_KEYS = [
    models.JOB_KEY,
    models.GIT_BRANCH_KEY,
    models.ARCHITECTURE_KEY,
    models.DEVICE_TYPE_KEY,
    models.DEFCONFIG_FULL_KEY,
]

TEST_GROUP_SPEC_KEYS = [
    models.JOB_KEY,
    models.GIT_BRANCH_KEY,
    models.ARCHITECTURE_KEY,
    models.DEVICE_TYPE_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.NAME_KEY,
    models.KERNEL_KEY,
]


def _test_case_regression_data(test_case, group):
    return {
        models.TEST_CASE_ID_KEY: test_case[models.ID_KEY],
        models.CREATED_KEY: test_case[models.CREATED_KEY],
        models.STATUS_KEY: test_case[models.STATUS_KEY],
        models.KERNEL_KEY: group[models.KERNEL_KEY],
        models.GIT_COMMIT_KEY: group[models.GIT_COMMIT_KEY],
    }


def _check_and_track(test_case, group, last_case, last_group, db, spec,
                     hierarchy):
    hierarchy = hierarchy + [test_case[models.NAME_KEY]]
    regr = {k: spec[k] for k in REGRESSION_SPEC_KEYS}
    regr[models.HIERARCHY_KEY] = hierarchy
    test_case_path = ".".join(hierarchy)

    if last_case[models.STATUS_KEY] == "PASS":
        utils.LOG.info("New regression: {}".format(test_case_path))
        regr[models.REGRESSIONS_KEY] = [
            _test_case_regression_data(case, group)
            for case, group in [(last_case, last_group), (test_case, group)]
        ]
        regr[models.KERNEL_KEY] = spec[models.KERNEL_KEY]
        doc = models.test_regression.TestRegressionDocument.from_json(regr)
        return utils.db.save(db, doc, manipulate=True) if doc else (500, None)

    regr[models.KERNEL_KEY] = last_group[models.KERNEL_KEY]
    regr_doc = utils.db.find_one2(db[models.TEST_REGRESSION_COLLECTION], regr)
    if not regr_doc:
        utils.LOG.info("Not tracking: {}".format(test_case_path))
        return (200, None)

    utils.LOG.info("Tracking regression: {}".format(test_case_path))
    test_case_data = _test_case_regression_data(test_case, group)
    regr_doc[models.REGRESSIONS_KEY].append(test_case_data)
    regr_doc[models.KERNEL_KEY] = spec[models.KERNEL_KEY]
    del regr_doc[models.ID_KEY]  # Save a separate doc for each kernel revision
    del regr_doc[models.CREATED_KEY]
    doc = models.test_regression.TestRegressionDocument.from_json(regr_doc)
    return utils.db.save(db, doc, manipulate=True) if doc else (500, None)


def _add_test_group_regressions(group, last_group, db, spec, hierarchy=None,
                                ids=None):
    if hierarchy is None:
        hierarchy = [group[models.NAME_KEY]]
    else:
        hierarchy = hierarchy + [group[models.NAME_KEY]]

    if ids is None:
        ids = []

    case_collection = db[models.TEST_CASE_COLLECTION]
    group_collection = db[models.TEST_GROUP_COLLECTION]

    def _get_docs_dict(group, collection, field):
        return {
            doc[models.NAME_KEY]: doc
            for doc in (utils.db.find_one2(collection, doc_id)
                        for doc_id in group[field])
        }

    def _get_cases_dict(group):
        return _get_docs_dict(group, case_collection, models.TEST_CASES_KEY)

    def _get_sub_groups_dict(group):
        return _get_docs_dict(group, group_collection, models.SUB_GROUPS_KEY)

    test_cases = _get_cases_dict(group)
    last_test_cases = _get_cases_dict(last_group) if last_group else {}

    for test_case_name, test_case in test_cases.iteritems():
        last_case = last_test_cases.get(test_case_name)
        if last_case and test_case[models.STATUS_KEY] == "FAIL":
            ret, doc_id = _check_and_track(
                test_case, group, last_case, last_group, db, spec, hierarchy)
            if doc_id:
                ids.append(doc_id)

    sub_groups = _get_sub_groups_dict(group)
    last_sub_groups = _get_sub_groups_dict(last_group) if last_group else {}

    for sub_name, sub in sub_groups.iteritems():
        last_sub = last_sub_groups.get(sub_name)
        _add_test_group_regressions(sub, last_sub, db, spec, hierarchy, ids)

    return ids


def find(group_id, db_options={}, db=None):
    """Find the regression starting from a single test group document.

    :param group_id: The id of the test group document.
    :type group_id: str
    :param db: The database connection.
    :type db: Database connection object.
    :return tuple The return value that can be 200 (success), 201 (document
    saved) or 500 (error); a list with the IDs of the test regression documents
    or None.
    """
    if not group_id:
        utils.LOG.warn("Not searching regressions as no test group ID")
        return (200, None)

    utils.LOG.info("Searching test regressions for '{}'".format(group_id))

    if db is None:
        db = utils.db.get_db_connection(db_options)
    collection = db[models.TEST_GROUP_COLLECTION]
    group = utils.db.find_one2(collection, group_id)

    if not group:
        utils.LOG.warn("Test group not found: {}".format(group_id))
        return (500, None)

    spec = {k: group[k] for k in TEST_GROUP_SPEC_KEYS}
    last_spec = {k: v for k, v in spec.iteritems() if k != models.KERNEL_KEY}
    last_spec[models.CREATED_KEY] = {"$lt": group[models.CREATED_KEY]}
    last = collection.find_one(last_spec, sort=[(models.CREATED_KEY, -1)])
    redis_conn = redisdb.get_db_connection(db_options)
    lock_key = "-".join(group[k] for k in TEST_GROUP_SPEC_KEYS)
    # Hold a lock as multiple group results may be imported in parallel
    with redis.lock.Lock(redis_conn, lock_key, timeout=5):
        regr_ids = _add_test_group_regressions(group, last, db, spec)
    return (200, regr_ids)
