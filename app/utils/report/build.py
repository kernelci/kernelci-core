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

"""Create the build email report."""

import gettext
import io
import pymongo

import models
import utils.db
import utils.report.common as rcommon

# Register the translation domain and fallback safely, at the moment we do
# not care if we have translations or not, we just use gettext to exploit its
# plural forms capabilities. We mark the email string as translatable though
# so we might give that feature in the future.
L10N = gettext.translation(models.I18N_DOMAIN, fallback=True)
# Register normal Unicode gettext.
G_ = L10N.ugettext
# Register plural forms Unicode gettext.
P_ = L10N.ungettext


BUILD_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.ERRORS_KEY,
    models.STATUS_KEY,
    models.WARNINGS_KEY
]

BUILD_SEARCH_SORT = [
    (models.DEFCONFIG_KEY, pymongo.ASCENDING),
    (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
    (models.ARCHITECTURE_KEY, pymongo.ASCENDING)
]


# pylint: disable=too-many-locals
# pylint: disable=star-args
def create_build_report(job, kernel, db_options, mail_options=None):
    """Create the build report email to be sent.

    :param job: The name of the job.
    :type job: str
    :param  kernel: The name of the kernel.
    :type kernel: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dict
    :return A tuple with the email body and subject as strings or None.
    """
    kwargs = {}
    email_body = None
    subject = None
    # This is used to provide a footer note in the email report.
    info_email = None

    fail_count = total_count = 0
    errors_count = warnings_count = 0
    fail_results = []

    if mail_options:
        info_email = mail_options.get("info_email", None)

    spec = {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel
    }

    database = utils.db.get_db_connection(db_options)
    total_results, total_count = utils.db.find_and_count(
        database[models.DEFCONFIG_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BUILD_SEARCH_FIELDS
    )

    err_data, errors_count, warnings_count = _get_errors_count(
        total_results.clone())

    unique_keys = [models.ARCHITECTURE_KEY]
    total_unique_data = rcommon.get_unique_data(
        total_results.clone(), unique_keys=unique_keys)

    git_commit, git_url, git_branch = rcommon.get_git_data(
        job, kernel, db_options)

    spec[models.STATUS_KEY] = models.FAIL_STATUS

    fail_results, fail_count = utils.db.find_and_count(
        database[models.DEFCONFIG_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BUILD_SEARCH_FIELDS,
        sort=BUILD_SEARCH_SORT)

    failed_data = _parse_build_data(fail_results.clone())

    kwargs = {
        "base_url": rcommon.DEFAULT_BASE_URL,
        "build_url": rcommon.DEFAULT_BUILD_URL,
        "error_data": err_data,
        "errors_count": errors_count,
        "fail_count": fail_count,
        "failed_data": failed_data,
        "git_branch": git_branch,
        "git_commit": git_commit,
        "git_url": git_url,
        "info_email": info_email,
        "pass_count": total_count - fail_count,
        "total_count": total_count,
        "total_unique_data": total_unique_data,
        "warnings_count": warnings_count,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
    }

    if all([fail_count == 0, total_count == 0]):
        utils.LOG.warn(
            "Nothing found for '%s-%s': no build email report sent",
            job, kernel)
    else:
        email_body, subject = _create_build_email(**kwargs)

    return email_body, subject


def _get_errors_count(results):
    """Parse the build data and get errors and warnings.

    :param results: The results to parse.
    :type results: pymongo.cursor.Cursor.
    :return The errors data structure, the errors and warnings count.
    """
    err_data = {}
    total_errors = total_warnings = 0

    arch_keys = err_data.viewkeys()

    for result in results:
        res_get = result.get

        arch = res_get(models.ARCHITECTURE_KEY)
        defconfig = res_get(models.DEFCONFIG_KEY)
        defconfig_full = res_get(models.DEFCONFIG_FULL_KEY, defconfig)
        res_errors = res_get(models.ERRORS_KEY, 0)
        res_warnings = res_get(models.WARNINGS_KEY, 0)

        if defconfig_full is None:
            defconfig_full = defconfig

        err_struct = {}

        if all([res_errors is not None, res_errors != 0]):
            total_errors += res_errors
            err_struct[models.ERRORS_KEY] = res_errors

        if all([res_warnings is not None, res_warnings != 0]):
            total_warnings += res_warnings
            err_struct[models.WARNINGS_KEY] = res_warnings

        if err_struct:
            if arch in arch_keys:
                if defconfig_full in err_data[arch].keys():
                    # Multiple builds with the same defconfig value?
                    err_data[arch][defconfig_full][models.WARNINGS_KEY] += \
                        res_warnings
                    err_data[arch][defconfig_full][models.ERRORS_KEY] += \
                        res_errors
                else:
                    err_data[arch][defconfig_full] = err_struct
            else:
                err_data[arch] = {}
                err_data[arch][defconfig_full] = err_struct

    return err_data, total_errors, total_warnings


def _parse_build_data(results):
    """Parse the build data to provide a writable data structure.

    Loop through the build data found, and create a new dictionary whose keys
    are the architectures and their values a list of tuples of
    (defconfig, status).

    :param results: The results to parse.
    :type results: pymongo.cursor.Cursor.
    :return A dictionary.
    """
    parsed_data = {}
    arch_keys = parsed_data.viewkeys()

    for result in results:
        res_get = result.get

        arch = res_get(models.ARCHITECTURE_KEY)
        defconfig_full = res_get(models.DEFCONFIG_FULL_KEY, None)
        defconfig = res_get(models.DEFCONFIG_KEY)
        status = res_get(models.STATUS_KEY)

        struct = ((defconfig_full or defconfig), status)

        if arch in arch_keys:
            parsed_data[arch].append(struct)
        else:
            parsed_data[arch] = []
            parsed_data[arch].append(struct)

    return parsed_data


# pylint: disable=too-many-statements
def _create_build_email(**kwargs):
    """Parse the results and create the email text body to send.

    :param job: The name of the job.
    :type job: str
    :param  kernel: The name of the kernel.
    :type kernel: str
    :param git_commit: The git commit.
    :type git_commit: str
    :param git_url: The git url.
    :type git_url: str
    :param git_branch: The git branch.
    :type git_branch: str
    :param failed_data: The parsed failed results.
    :type failed_data: dict
    :param fail_count: The total number of failed results.
    :type fail_count: int
    :param total_count: The total number of results.
    :type total_count: int
    :param total_unique_data: The unique values data structure.
    :type total_unique_data: dictionary
    :param pass_count: The total number of passed results.
    :type pass_count: int
    :param base_url: The base URL to build the dashboard links.
    :type base_url: string
    :param boot_url: The base URL for the boot section of the dashboard.
    :type boot_url: string
    :param build_url: The base URL for the build section of the dashboard.
    :type build_url: string
    :param info_email: The email address for the footer note.
    :type info_email: string
    :return A tuple with the email body and subject as strings.
    """
    k_get = kwargs.get
    total_unique_data = k_get("total_unique_data", None)
    failed_data = k_get("failed_data", None)
    info_email = k_get("info_email", None)
    fail_count = k_get("fail_count", 0)
    warnings_count = k_get("warnings_count", 0)
    errors_count = k_get("errors_count", 0)
    error_data = k_get("error_data", None)

    email_body = u""
    subject_str = _get_build_subject_string(**kwargs)

    built_unique_one = G_(u"Built: %s")

    built_unique_string = None
    if total_unique_data:
        unique_archs = rcommon.count_unique(
            total_unique_data.get("arch", None))

        kwargs["unique_archs"] = unique_archs

        arch_str = P_(
            u"%(unique_archs)d unique architecture",
            u"%(unique_archs)d unique architectures",
            unique_archs
        )

        if unique_archs > 0:
            built_unique_string = built_unique_one % arch_str

        if built_unique_string:
            built_unique_string = built_unique_string % kwargs

    build_summary_url = u"%(build_url)s/%(job)s/kernel/%(kernel)s/" % kwargs

    tree = G_(u"Tree: %(job)s\n") % kwargs
    branch = G_(u"Branch: %(git_branch)s\n") % kwargs
    git_describe = G_(u"Git Describe: %(kernel)s\n") % kwargs
    git_commit = G_(u"Git Commit: %(git_commit)s\n") % kwargs
    git_url = G_(u"Git URL: %(git_url)s\n") % kwargs

    with io.StringIO() as m_string:
        m_string.write(subject_str)
        m_string.write(u"\n")
        m_string.write(u"\n")
        m_string.write(
            G_(u"Full Build Summary: %s\n") % build_summary_url)
        m_string.write(u"\n")
        m_string.write(tree)
        m_string.write(branch)
        m_string.write(git_describe)
        m_string.write(git_commit)
        m_string.write(git_url)

        if built_unique_string:
            m_string.write(built_unique_string)
            m_string.write(u"\n")

        if failed_data:
            m_string.write(u"\n")
            m_string.write(
                P_(
                    u"Build Failure Detected:\n",
                    u"Build Failures Detected:\n", fail_count
                ))

            f_get = failed_data.get
            for arch in failed_data.viewkeys():
                m_string.write(u"\n")
                m_string.write(
                    G_(u"%s:\n") % arch
                )

                for struct in f_get(arch):
                    m_string.write(u"\n")
                    m_string.write(
                        G_(u"    %s: %s") % (struct[0], struct[1])
                    )
                m_string.write(u"\n")

        if error_data:
            m_string.write(u"\n")

            if all([errors_count > 0, warnings_count > 0]):
                m_string.write(G_(u"Errors and Warnings Detected:\n"))
            elif all([errors_count > 0, warnings_count == 0]):
                m_string.write(G_(u"Errors Detected:\n"))
            elif all([errors_count == 0, warnings_count > 0]):
                m_string.write(G_(u"Warnings Detected:\n"))

            m_string.write(u"\n")

            if any([errors_count > 0, warnings_count > 0]):
                err_get = error_data.get

                for arch in error_data.viewkeys():
                    m_string.write(G_(u"%s:") % arch)
                    m_string.write(u"\n\n")

                    for defconfig in err_get(arch).viewkeys():
                        err_numb = err_get(arch)[defconfig].get(
                            models.ERRORS_KEY, 0)
                        warn_numb = err_get(arch)[defconfig].get(
                            models.WARNINGS_KEY, 0)

                        err_string = P_(
                            u"%(errors)s error",
                            u"%(errors)s errors", err_numb)
                        warn_string = P_(
                            u"%(warnings)s warning",
                            u"%(warnings)s warnings", warn_numb)

                        substitutions = {
                            "defconfig": defconfig,
                            "err_string": err_string,
                            "errrors": err_numb,
                            "warn_string": warn_string,
                            "warnings": warn_numb
                        }

                        if all([err_numb > 0, warn_numb > 0]):
                            desc_string = G_(
                                u"%(err_string)s, %(warn_string)s")
                        elif all([err_numb > 0, warn_numb == 0]):
                            desc_string = u"%(err_string)s"
                        elif all([err_numb == 0, warn_numb > 0]):
                            desc_string = u"%(warn_string)s"

                        desc_string = desc_string % substitutions
                        substitutions["desc_string"] = desc_string

                        defconfig_string = (
                            G_(u"    %(defconfig)s: %(desc_string)s") %
                            substitutions)

                        m_string.write(defconfig_string % substitutions)
                        m_string.write(u"\n")

                    m_string.write(u"\n")

        if info_email:
            m_string.write(u"\n")
            m_string.write(u"---\n")
            m_string.write(G_(u"For more info write to <%s>") % info_email)

        email_body = m_string.getvalue()

    return email_body, subject_str


def _get_build_subject_string(**kwargs):
    """Create the build email subject line.

    This is used to created the custom email report line based on the number
    of values we have.

    :param total_count: The total number of build reports.
    :type total_count: integer
    :param fail_count: The number of failed build reports.
    :type fail_count: integer
    :param pass_count: The number of successful build reports.
    :type pass_count: integer
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    :return The subject string.
    """
    k_get = kwargs.get
    fail_count = k_get("fail_count", 0)
    total_count = k_get("total_count", 0)
    errors = k_get("errors_count", 0)
    warnings = k_get("warnings_count", 0)

    subject_str = u""

    base_subject = G_(u"%(job)s build")
    kernel_name = G_(u"(%(kernel)s)")
    failed_builds = G_(u"%(fail_count)d failed")
    passed_builds = G_(u"%(pass_count)d passed")
    total_builds = P_(
        u"%(total_count)d build", u"%(total_count)d builds", total_count)
    errors_string = P_(
        u"%(errors_count)d error", u"%(errors_count)d errors", errors)
    warnings_string = P_(
        u"%(warnings_count)d warning",
        u"%(warnings_count)d warnings", warnings)

    subject_substitutions = {
        "build_name": base_subject,
        "errors_string": errors_string,
        "failed_builds": failed_builds,
        "kernel_name": kernel_name,
        "passed_builds": passed_builds,
        "total_builds": total_builds,
        "warnings_string": warnings_string
    }

    if all([fail_count == 0, total_count != 0, errors == 0, warnings == 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s "
            "%(kernel_name)s"
        )
    elif all([fail_count == 0, total_count != 0, errors == 0, warnings != 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s, "
            "%(warnings_string)s %(kernel_name)s"
        )
    elif all([fail_count == 0, total_count != 0, errors != 0, warnings != 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s, "
            "%(errors_string)s, %(warnings_string)s %(kernel_name)s"
        )
    elif all([fail_count == 0, total_count != 0, errors != 0, warnings == 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s, "
            "%(errors_string)s %(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count != total_count, errors == 0, warnings != 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s, "
            "%(failed_builds)s, %(warnings_string)s %(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count != total_count, errors != 0, warnings != 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s, "
            "%(failed_builds)s, %(errors_string)s, %(warnings_string)s "
            "%(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count != total_count, errors != 0, warnings == 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s, "
            "%(failed_builds)s, %(errors_string)s, "
            "%(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count != total_count, errors == 0, warnings == 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(passed_builds)s, "
            "%(failed_builds)s %(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count == total_count, errors == 0, warnings == 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(failed_builds)s "
            "%(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count == total_count, errors == 0, warnings != 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(failed_builds)s "
            "%(warnings_string)s %(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count == total_count, errors != 0, warnings != 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(failed_builds)s "
            "%(errors_string)s, %(warnings_string)s %(kernel_name)s"
        )
    elif all([
            fail_count != 0,
            fail_count == total_count, errors != 0, warnings == 0]):
        subject_str = G_(
            u"%(build_name)s: %(total_builds)s: %(failed_builds)s "
            "%(errors_string)s %(kernel_name)s"
        )

    # Perform all the normal placeholder substitutions.
    subject_str = subject_str % subject_substitutions
    # Now fill in the values.
    subject_str = subject_str % kwargs

    return subject_str
