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

"""Functions to import builds/defconfigs."""

try:
    import simplejson as json
except ImportError:
    import json

try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk

import bson
import datetime
import glob
import os
import pymongo.errors
import re
import redis
import types

import models
import models.build as mbuild
import models.job as mjob
import utils
import utils.database.redisdb as redisdb
import utils.db
import utils.elf as elf
import utils.errors

ERR_ADD = utils.errors.add_error
ERR_UPDATE = utils.errors.update_errors

# Regex to extract the kernel version.
# Should match strings that begins as:
# 4.1-1234-g12345
# 4.1.14-rc8-1234-g12345
# The 'rc*' pattern is part of the kernel version.
# TODO: add patches count extraction as well.
KERNEL_VERSION_MATCH = re.compile(r"^(?P<version>\d+\.{1}\d+(?:\.{1}\d+)?)")
KERNEL_RC_VERSION_MATCH = re.compile(
    r"^(?P<version>\d+\.{1}\d+(?:\.{1}\d+)?-{1}rc\d*)")

# Regex to extract compiler information from the compiler string.
# Example strings are:
# gcc version 4.7.3 (Ubuntu/Linaro 4.7.3-12ubuntu1)
# Apple LLVM version 7.0.2 (clang-700.1.81)
# Debian clang version 3.5.0-10 (tags/RELEASE_350/final) (based on LLVM 3.5.0)
COMPILER_MATCH = re.compile(
    r"^(?P<compiler>[\w\s?]+)\s{1}version\s{1}"
    r"(?P<compiler_version>\d+\.{1}\d+(?:\.{1}\d+)?(?:\-{1}\d+)?)"
)


def get_artifacts_size(artifacts, build_dir):
    """Return artifact file size.

    :param artifacts: The dictionary with the key to return and the value to
    get the size of.
    :type artifacts: dict
    :param build_dir: The real path of the build directory.
    :type build_dir: str
    :return Yield 2-tuples with the key to set and its value.
    """
    for k, v in artifacts.iteritems():
        if v:
            artifact = os.path.join(build_dir, v)
            if os.path.isfile(artifact):
                yield k, os.stat(artifact).st_size


def parse_dtb_dir(build_dir, dtb_dir):
    """Parse the dtb directory of a build and return its contents.

    :param build_dir: The directory of the build that containes the dtb one.
    :type build_dir: string
    :param dtb_dir: The name of the dtb directory.
    :type dtb_dir: string
    :return A list with the relative path to the files contained in the dtb
    directory.
    """
    dtb_data = []
    d_dir = os.path.join(build_dir, dtb_dir)
    for dirname, _, files in walk(d_dir):
        if not dirname.startswith("."):
            rel = os.path.relpath(dirname, d_dir)
            if rel == ".":
                rel = ""
            for dtb_file in files:
                if not dtb_file.startswith("."):
                    dtb_data.append(os.path.join(rel, dtb_file))
    return dtb_data


def _search_prev_build_doc(build_doc, database):
    """Search for a similar defconfig document in the database.

    Search for an already imported defconfig/build document in the database
    and return its object ID and creation date. This is done to make sure
    we do not create double documents when re-importing the same data or
    updating it.

    :param build_doc: The new defconfig document.
    :param database: The db connection.
    :return The previous doc ID and its creation date, or None.
    """
    doc_id = None
    c_date = None

    if all([build_doc, database]):
        spec = {
            models.JOB_KEY: build_doc.job,
            models.KERNEL_KEY: build_doc.kernel,
            models.DEFCONFIG_KEY: build_doc.defconfig,
            models.DEFCONFIG_FULL_KEY: build_doc.defconfig_full,
            models.ARCHITECTURE_KEY: build_doc.arch
        }
        prev_doc = utils.db.find(
            database[models.BUILD_COLLECTION],
            10,
            0,
            spec=spec,
            fields=[models.ID_KEY, models.CREATED_KEY]
        )

        prev_doc_count = prev_doc.count()
        if prev_doc_count > 0:
            if prev_doc_count == 1:
                doc_id = prev_doc[0].get(models.ID_KEY, None)
                c_date = prev_doc[0].get(models.CREATED_KEY, None)
            else:
                utils.LOG.warn(
                    "Found multiple defconfig docs matching: %s",
                    spec)
                utils.LOG.error(
                    "Cannot keep old document ID, don't know which one to "
                    "use!")

    return doc_id, c_date


def _extract_compiler_data(compiler_version_full):
    """Extract the compiler name and version from a compiler string.

    :param compiler_version_full: The full compiler string, its description.
    :type compiler_version_full: str
    :return A 3-tuple: compiler, compiler_version, compiler_version_full.
    """
    compiler = None
    compiler_version = None
    compiler_version_ext = None

    if compiler_version_full:
        compiler_version_full = compiler_version_full.strip()

        matched = COMPILER_MATCH.match(compiler_version_full)
        if matched:
            compiler = matched.group("compiler").strip()
            compiler_version = matched.group("compiler_version").strip()
            compiler_version_ext = "{0:s} {1:s}".format(
                compiler, compiler_version)
    else:
        # Force it at None, in case we get an empty string.
        compiler_version_full = None

    return (compiler,
            compiler_version, compiler_version_ext, compiler_version_full)


def _extract_kernel_version(git_describe_v, git_describe):
    """Extract the actual kernel version number.

    For now, it simply splits the git_describe version and pick the first
    value

    :param git_describe_v: The value of the git_describe_v key.
    :type git_describe_v: str
    :param git_describe: The value of the git_describe key.
    :type git_describe: str
    :return The extracted kernel version.
    """
    to_extract = git_describe_v
    kernel_version = None

    if not to_extract:
        to_extract = git_describe

    if to_extract:
        if to_extract[0] == "v":
            to_extract = to_extract[1:]

        if "rc" in to_extract:
            matcher = KERNEL_RC_VERSION_MATCH
        else:
            matcher = KERNEL_VERSION_MATCH

        matched = matcher.match(to_extract)
        if matched:
            kernel_version = matched.group("version")

    return kernel_version


class BuildError(Exception):
    def __init__(self, code, *args, **kwargs):
        self.code = code
        self.from_exc = kwargs.pop('from_exc', None)
        super(BuildError, self).__init__(*args, **kwargs)


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def parse_build_data(build_data, job, kernel, build_dir=None):
    """Parse the json build data and craete the corresponding document.

    :param build_data: The json build data.
    :type build_data: dictionary
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    :param errors: The errors data structure.
    :type errors: dictionary
    :param build_dir: Full path to the build directory.
    :type build_dir: string
    :return A 2-tuple: (BuildDocument, a "artifact type": "artifact name"
    dictionary)
    """
    if not isinstance(build_data, types.DictionaryType):
        raise BuildError(500, "JSON data is not a dictionary")

    try:
        defconfig = build_data[models.DEFCONFIG_KEY]
        d_job = build_data.get(models.JOB_KEY, job)
        d_kernel = build_data.get(models.KERNEL_KEY, kernel)
        defconfig_full = build_data.get(models.DEFCONFIG_FULL_KEY, None)
        kconfig_fragments = build_data.get(
            models.KCONFIG_FRAGMENTS_KEY, None)

        defconfig_full = utils.get_defconfig_full(
            build_dir, defconfig, defconfig_full, kconfig_fragments)

        build_doc = mbuild.BuildDocument(
            d_job, d_kernel, defconfig, defconfig_full=defconfig_full)

        build_doc.dirname = build_dir
        build_doc.arch = build_data.get(models.ARCHITECTURE_KEY, None)
        build_doc.build_log = build_data.get(models.BUILD_LOG_KEY, None)
        build_doc.build_platform = build_data.get(
            models.BUILD_PLATFORM_KEY, [])
        build_doc.build_time = build_data.get(models.BUILD_TIME_KEY, 0)
        build_doc.build_type = build_data.get(
            models.BUILD_TYPE_KEY, models.KERNEL_BUILD_TYPE)
        build_doc.dtb_dir = build_data.get(models.DTB_DIR_KEY, None)
        build_doc.errors = build_data.get(models.BUILD_ERRORS_KEY, 0)
        build_doc.file_server_resource = build_data.get(
            models.FILE_SERVER_RESOURCE_KEY, None)
        build_doc.file_server_url = build_data.get(
            models.FILE_SERVER_URL_KEY, None)
        build_doc.git_branch = build_data.get(
            models.GIT_BRANCH_KEY, None)
        build_doc.git_commit = build_data.get(
            models.GIT_COMMIT_KEY, None)
        build_doc.git_describe = build_data.get(
            models.GIT_DESCRIBE_KEY, None)
        build_doc.git_url = build_data.get(models.GIT_URL_KEY, None)
        build_doc.kconfig_fragments = kconfig_fragments
        build_doc.kernel_config = build_data.get(
            models.KERNEL_CONFIG_KEY, None)
        build_doc.kernel_image = build_data.get(
            models.KERNEL_IMAGE_KEY, None)
        build_doc.modules = build_data.get(models.MODULES_KEY, None)
        build_doc.modules_dir = build_data.get(
            models.MODULES_DIR_KEY, None)
        build_doc.status = build_data.get(
            models.BUILD_RESULT_KEY, models.UNKNOWN_STATUS)
        build_doc.system_map = build_data.get(
            models.SYSTEM_MAP_KEY, None)
        build_doc.text_offset = build_data.get(
            models.TEXT_OFFSET_KEY, None)
        build_doc.version = build_data.get(models.VERSION_KEY, "1.0")
        build_doc.warnings = build_data.get(models.BUILD_WARNINGS_KEY, 0)
        build_doc.kernel_image_size = build_data.get(
            models.KERNEL_IMAGE_SIZE_KEY, None)
        build_doc.modules_size = build_data.get(models.MODULES_SIZE_KEY, None)
        build_doc.cross_compile = build_data.get(models.CROSS_COMPILE_KEY, None)

        build_doc.git_describe_v = build_data.get(
            models.GIT_DESCRIBE_V_KEY, None)
        build_doc.kernel_version = _extract_kernel_version(
            build_doc.git_describe_v, build_doc.git_describe)

        compiler_version_full = (
            build_data.get(models.COMPILER_VERSION_FULL_KEY, None) or
            build_data.get(models.COMPILER_VERSION_KEY, None))

        compiler_data = _extract_compiler_data(compiler_version_full)
        build_doc.compiler = compiler_data[0]
        build_doc.compiler_version = compiler_data[1]
        build_doc.compiler_version_ext = compiler_data[2]
        build_doc.compiler_version_full = compiler_data[3]

        artifacts = {
            models.BUILD_LOG_SIZE_KEY: build_doc.build_log,
            models.KERNEL_CONFIG_SIZE_KEY: build_doc.kernel_config,
            models.KERNEL_IMAGE_SIZE_KEY: build_doc.kernel_image,
            models.MODULES_SIZE_KEY: build_doc.modules,
            models.SYSTEM_MAP_SIZE_KEY: build_doc.system_map,
            models.VMLINUX_FILE_SIZE_KEY:
                build_data.get(models.VMLINUX_FILE_KEY, None)
        }
    except KeyError, ex:
        raise BuildError(500,
            "Missing mandatory key '%s' in build data (job: %s, kernel: %s)" \
            % (ex.args[0], job, kernel),
            from_exc=ex)

    return build_doc, artifacts


# pylint: disable=too-many-arguments
def _traverse_build_dir(
        build_dir,
        kernel_dir, job, kernel, job_id, job_date, errors, database):
    """Traverse the build directory looking for the build file.

    :param build_dir: The name of the build directory.
    :type build_dir: string
    :param kernel_dir: The full path to the kernel directory.
    :type kernel_dir: string
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    :param job_id: The ID of the job this build belongs to.
    :type job_id: bson.objectid.ObjectId
    :param job_date: The job document creation date.
    :type job_date: datetime.datetime
    :param errors: The errors data structure.
    :type errors: dictionary
    :param database: The database connection.
    :return A BuildDocument or None.
    """
    real_dir = os.path.join(kernel_dir, build_dir)

    def _scan_build_dir():
        """Yield the files found in the build directory."""
        for entry in scandir(real_dir):
            if entry.is_file() and entry.name == models.BUILD_META_JSON_FILE:
                yield entry.name

    utils.LOG.info("Traversing %s-%s-%s", job, kernel, build_dir)
    for data_file in _scan_build_dir():
        try:
            with open(os.path.join(real_dir, data_file)) as data:
                build_data = json.load(data)
        except IOError, ex:
            err_msg = "Error reading json data file (job: %s, kernel: %s) - %s"
            utils.LOG.exception(ex)
            utils.LOG.error(err_msg, job, kernel, build_dir)
            ERR_ADD(errors, 500, err_msg % (job, kernel, build_dir))
            continue
        except json.JSONDecodeError, ex:
            err_msg = "Error loading json data (job: %s, kernel: %s) - %s"
            utils.LOG.exception(ex)
            utils.LOG.error(err_msg, job, kernel, build_dir)
            ERR_ADD(errors, 500, err_msg % (job, kernel, build_dir))
            continue

        try:
            build_doc, artifacts = parse_build_data(
                build_data, job, kernel, build_dir=real_dir)
        except BuildError as e:
            if e.from_exc:
                utils.LOG.exception(e.from_exc)
            utils.LOG.error(e.args[0])
            ERR_ADD(errors, e.code, e.args[0])
            continue

        build_doc.job_id = job_id
        # Search for previous defconfig doc. This is only useful when
        # re-importing data and we want to have the same ID as before.
        doc_id, c_date = _search_prev_build_doc(
            build_doc, database)
        build_doc.id = doc_id
        if c_date:
            build_doc.created_on = c_date
        else:
            # XXX: we used to give defconfig the job date.
            build_doc.created_on = datetime.datetime.now(
                tz=bson.tz_util.utc)

        if build_doc.dtb_dir:
            build_doc.dtb_dir_data = parse_dtb_dir(
                real_dir, build_doc.dtb_dir)

        if artifacts:
            for key, size in get_artifacts_size(artifacts, real_dir):
                setattr(build_doc, key, size)

            vmlinux = artifacts.get(models.VMLINUX_FILE_SIZE_KEY, None)
            if vmlinux:
                values = elf.read(os.path.join(build_dir, vmlinux))
                for k, v in values.iteritems():
                    setattr(build_doc, k, v)
        return build_doc


def _traverse_kernel_dir(
        kernel_dir, job, kernel, job_id, job_date, database, scan_func=None):
    """Traverse the kernel directory looking for the build directories.

    :param kernel_dir: The full path to the kernel directory.
    :type kernel_dir: string
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    :param job_id: The ID of the job this build belongs to.
    :type job_id: bson.objectid.ObjectId
    :param job_date: The job document creation date.
    :type job_date: datetime.datetime
    :param errors: The errors data structure.
    :type errors: dictionary
    :param database: The database connection.
    :param scan_func: Function to scan a directory yielding its subdirs. It
    must accept a single argument: the full path of the directory to scan.
    :type scan_func: function
    :return A 3-tuple: the list of BuildDocument objects, the job status
    value and the errors data structure.
    """
    job_status = models.UNKNOWN_STATUS
    errors = {}
    docs = []

    def _scan_kernel_dir(to_scan):
        """Yields the directory contained in the kernel one.

        :param to_scan: Full path of the directory to scan.
        :type to_scan: string
        :return The name of the subdirectories if they do not start with "." or
        are not a lab directory.
        """
        for entry in scandir(to_scan):
            if all([entry.is_dir(),
                    not entry.name.startswith("."),
                    not utils.is_lab_dir(entry.name)]):
                yield entry.name

    def _get_build_documents():
        """Generator to traverse the build dir and retrieve the documents."""
        for build_dir in scan_func(kernel_dir):
            doc = _traverse_build_dir(
                build_dir,
                kernel_dir, job, kernel, job_id, job_date, errors, database)
            if doc is not None:
                yield doc

    if scan_func is None:
        scan_func = _scan_kernel_dir

    job_status = models.BUILD_STATUS
    if os.path.isdir(kernel_dir):
        done_file = os.path.join(kernel_dir, models.DONE_FILE)
        done_file_p = os.path.join(kernel_dir, models.DONE_FILE_PATTERN)

        if any([os.path.exists(done_file), glob.glob(done_file_p)]):
            job_status = models.PASS_STATUS

        docs = [doc for doc in _get_build_documents()]

    return docs, job_status, errors


def _update_job_doc(job_doc, job_id, status, docs, database):
    """Update the JobDocument with values from a BuildDocument.

    :param job_doc: The job document to update.
    :type job_doc: JobDocument
    :param status: The job status value.
    :type status: string
    :param docs: The list of BuildDocument objects.
    :type docs: list
    """
    to_update = False
    ret_val = 201

    if all([job_id, job_doc.id != job_id]):
        job_doc.id = job_id
        to_update = True

    if job_doc.status != status:
        job_doc.status = status
        to_update = True

    no_git = all([
        not job_doc.git_url,
        not job_doc.git_commit,
        not job_doc.git_branch,
        not job_doc.git_describe,
        not job_doc.git_describe_v
    ])

    no_compiler = all([
        not job_doc.compiler,
        not job_doc.compiler_version,
        not job_doc.compiler_version_ext,
        not job_doc.compiler_version_full,
        not job_doc.cross_compile
    ])

    if all([docs, no_git, no_compiler]):
        # Kind of a hack:
        # We want to store some metadata at the job document level as well,
        # like git tree, git commit...
        # Since, at the moment, we do not have the metadata file at the job
        # level we need to pick one from the build documents, and extract some
        # values.
        docs_len = len(docs)
        idx = 0
        while idx < docs_len:
            d_doc = docs[idx]
            if isinstance(d_doc, mbuild.BuildDocument):
                if all([d_doc.job == job_doc.job,
                        d_doc.kernel == job_doc.kernel]):
                    job_doc.git_branch = d_doc.git_branch
                    job_doc.git_commit = d_doc.git_commit
                    job_doc.git_describe = d_doc.git_describe
                    job_doc.git_describe_v = d_doc.git_describe_v
                    job_doc.kernel_version = d_doc.kernel_version
                    job_doc.git_url = d_doc.git_url
                    job_doc.compiler = d_doc.compiler
                    job_doc.compiler_version = d_doc.compiler_version
                    job_doc.compiler_version_ext = d_doc.compiler_version_ext
                    job_doc.compiler_version_full = d_doc.compiler_version_full
                    job_doc.cross_compile = d_doc.cross_compile
                    to_update = True
                    break

            idx += 1

    if to_update:
        ret_val, _ = utils.db.save(database, job_doc)
    return ret_val


def _import_builds(job, kernel, db_options, base_path):
    """Execute the actual import and save operations.

    :param job: The job name.
    :type job: string
    :param kernel: The kernel name.
    :type kernel: string
    :param db_options: The database connection options.
    :type db_options: dictionary
    :param base_path: The base path on the file system.
    :type base_path: string
    :return A 3-tuple: The list of BuildDocument objects, the ID of the
    JobDocument object, the errors data structure.
    """
    docs = None
    job_id = None
    errors = {}

    if all([utils.valid_name(job), utils.valid_name(kernel)]):
        job_dir = os.path.join(base_path, job)
        kernel_dir = os.path.join(job_dir, kernel)

        if os.path.isdir(kernel_dir):
            try:
                p_doc = None
                database = None
                ret_val = 201

                database = utils.db.get_db_connection(db_options)
                p_doc = utils.db.find_one2(
                    database[models.JOB_COLLECTION],
                    {models.JOB_KEY: job, models.KERNEL_KEY: kernel})

                if p_doc:
                    job_doc = mjob.JobDocument.from_json(p_doc)
                    job_id = job_doc.id
                else:
                    job_doc = mjob.JobDocument(job, kernel)
                    job_doc.created_on = datetime.datetime.now(
                        tz=bson.tz_util.utc)
                    ret_val, job_id = utils.db.save(
                        database, job_doc, manipulate=True)

                if all([ret_val != 201, job_id is None]):
                    err_msg = (
                        "Error saving/finding job document for '%s-%s': "
                        "builds document might not be linked to their job")
                    utils.LOG.error(err_msg, job, kernel)
                    ERR_ADD(errors, ret_val, err_msg % (job, kernel))

                docs, j_status, errs = _traverse_kernel_dir(
                    kernel_dir,
                    job, kernel, job_id, job_doc.created_on, database)
                ERR_UPDATE(errors, errs)

                ret_val = _update_job_doc(
                    job_doc, job_id, j_status, docs, database)
                if ret_val != 201:
                    err_msg = (
                        "Error updating job document '%s-%s' with values from "
                        "build doc")
                    utils.LOG.error(err_msg, job, kernel)
                    ERR_ADD(errors, ret_val, err_msg % (job, kernel))
            except pymongo.errors.ConnectionFailure, ex:
                utils.LOG.exception(ex)
                utils.LOG.error("Error getting database connection")
                utils.LOG.warn(
                    "Builds for '%s-%s' will not be imported", job, kernel)
                ERR_ADD(
                    errors,
                    500,
                    "Internal server error: builds for '%s-%s' will not "
                    "be imported" % (job, kernel)
                )
        else:
            err_msg = (
                "Kernel directory for '%s-%s' does not exists: builds will "
                "not be imported. Has everything been uploaded?")
            utils.LOG.error(err_msg, job, kernel)
            ERR_ADD(errors, 500, err_msg % (job, kernel))
    else:
        err_msg = (
            "Wrong name for job and/or kernel value (%s-%s). "
            "Names cannot start with '.' and cannot contain '$' and '/'")
        utils.LOG.error(err_msg, job, kernel)
        ERR_ADD(errors, 500, err_msg % (job, kernel))

    return docs, job_id, errors


def import_multiple_builds(json_obj, db_options, base_path=utils.BASE_PATH):
    """Import builds from a file system directory based on the json data.

    :param json_obj: The json object with job and kernel values.
    :type json_obj: dictionary
    :param db_options: The database connection options.
    :type db_options: dictionary
    :param base_path: The base path on the file system where to look for.
    :type base_path: string
    :return The job ID value and the errors data structure.
    """
    errors = {}
    job = json_obj[models.JOB_KEY]
    kernel = json_obj[models.KERNEL_KEY]

    docs, job_id, errs = _import_builds(job, kernel, db_options, base_path)
    if docs:
        utils.LOG.info("Saving documents with job ID '%s'", job_id)
        try:
            database = utils.db.get_db_connection(db_options)
            ret_val, _ = utils.db.save_all(database, docs, manipulate=True)
            if ret_val != 201:
                ERR_ADD(
                    errors, ret_val,
                    "Error saving builds with job ID '%s'" % job_id)
        except pymongo.errors.ConnectionFailure, ex:
            utils.LOG.exception(ex)
            utils.LOG.error("Error getting database connection")
            ERR_ADD(errors, 500, "Error connecting to the database")

    ERR_UPDATE(errors, errs)
    return job_id, errors


def _get_or_create_job(job, kernel, database, db_options):
    """Get or create a job in the database.

    :param job: The name of the job.
    :type job: str
    :param kernel: The name of the kernel.
    :type kernel: str
    :param database: The mongodb database connection.
    :param db_options: The database connection options.
    :type db_options: dict
    :return a 3-tuple: return value, job document and job ID.
    """
    ret_val = 201
    job_doc = None
    job_id = None

    redis_conn = redisdb.get_db_connection(db_options)

    # We might be importing build in parallel through multi-processes.
    # Keep a lock here when looking for a job or we might end up with
    # multiple job creations.
    lock_key = "buil-import-{:s}-{:s}".format(job, kernel)
    with redis.lock.Lock(redis_conn, lock_key, timeout=5):
        p_doc = utils.db.find_one2(
            database[models.JOB_COLLECTION],
            {models.JOB_KEY: job, models.KERNEL_KEY: kernel})

        if p_doc:
            job_doc = mjob.JobDocument.from_json(p_doc)
            job_id = job_doc.id
        else:
            job_doc = mjob.JobDocument(job, kernel)
            job_doc.status = models.BUILD_STATUS
            job_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
            ret_val, job_id = utils.db.save(
                database, job_doc, manipulate=True)

    return ret_val, job_doc, job_id


def import_single_build(json_obj, db_options, base_path=utils.BASE_PATH):
    """Import a single build from the file system.

    :param json_obj: The json object containing the necessary data.
    :type json_obj: dictionary
    :param db_options: The database connection options.
    :type db_options: dictionary
    :param base_path: The base path on the file system where to look for.
    :type base_path: string
    :return The defconfig ID, the job ID and the errors data structure.
    """
    errors = {}
    job_id = None
    build_doc = None
    build_id = None
    j_get = json_obj.get

    arch = j_get(models.ARCHITECTURE_KEY)
    job = j_get(models.JOB_KEY)
    kernel = j_get(models.KERNEL_KEY)
    defconfig = j_get(models.DEFCONFIG_KEY)
    defconfig_full = j_get(models.DEFCONFIG_FULL_KEY, None)

    if all([utils.valid_name(job), utils.valid_name(kernel)]):
        job_dir = os.path.join(base_path, job)
        kernel_dir = os.path.join(job_dir, kernel)

        build_rel_dir = "%s-%s" % (arch, defconfig_full or defconfig)
        build_dir = os.path.join(kernel_dir, build_rel_dir)

        if os.path.isdir(build_dir):
            try:
                database = utils.db.get_db_connection(db_options)

                ret_val, job_doc, job_id = _get_or_create_job(
                    job, kernel, database, db_options)
                if ret_val != 201 and job_id is None:
                    err_msg = (
                        "Error saving/finding job document '%s-%s': "
                        "build document '%s-%s-%s-%s' might not be linked to "
                        "its job"
                    )
                    utils.LOG.error(
                        err_msg, job, kernel, job, kernel, arch, defconfig)
                    ERR_ADD(
                        errors,
                        ret_val,
                        err_msg % (job, kernel, job, kernel, arch, defconfig)
                    )

                build_doc = _traverse_build_dir(
                    build_dir,
                    kernel_dir,
                    job, kernel, job_id, job_doc.created_on, errors, database)

                ret_val = _update_job_doc(
                    job_doc,
                    job_id, job_doc.status, [build_doc], database)
                if ret_val != 201:
                    err_msg = (
                        "Error updating job document '%s-%s' with values from "
                        "build doc")
                    utils.LOG.error(err_msg, job, kernel)
                    ERR_ADD(errors, ret_val, err_msg % (job, kernel))
                if build_doc:
                    ret_val, build_id = utils.db.save(
                        database, build_doc, manipulate=True)
                if ret_val != 201:
                    err_msg = "Error saving build document '%s-%s-%s-%s'"
                    utils.LOG.error(err_msg, job, kernel, arch, defconfig)
                    ERR_ADD(
                        errors,
                        ret_val, err_msg % (job, kernel, arch, defconfig))
            except pymongo.errors.ConnectionFailure, ex:
                utils.LOG.exception(ex)
                utils.LOG.error("Error getting database connection")
                utils.LOG.warn(
                    "Build for '%s-%s-%s-%s' will not be imported",
                    job, kernel, arch, defconfig)
                ERR_ADD(
                    errors, 500,
                    "Internal server error: build for '%s-%s-%s-%s' "
                    "will not be imported" % (job, kernel, arch, defconfig)
                )
        else:
            err_msg = (
                "No build directory found for '%s-%s-%s-%s': "
                "has everything been uploaded?")
            utils.LOG.error(err_msg, job, kernel, arch, defconfig)
            ERR_ADD(errors, 500, err_msg % (job, kernel, arch, defconfig))
    else:
        err_msg = (
            "Wrong name for job and/or kernel value (%s-%s). "
            "Names cannot start with '.' and cannot contain '$' and '/'")
        utils.LOG.error(err_msg, job, kernel)
        ERR_ADD(errors, 500, err_msg % (job, kernel))
    return build_id, job_id, errors
