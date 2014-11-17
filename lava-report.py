#!/usr/bin/python
# <variable> = required
# Usage ./lava-report.py <option> [json]
import argparse
import subprocess
import re
from utils import *


def parse_json(json):
    jobs = load_json(json)
    url = validate_input(jobs['username'], jobs['token'], jobs['server'])
    connection = connect(url)
    duration = jobs['duration']
    # Remove unused data
    jobs.pop('duration')
    jobs.pop('username')
    jobs.pop('token')
    jobs.pop('server')
    return connection, jobs, duration


def boot_report(args):
    connection, jobs, duration =  parse_json(args.boot)
    results_directory = os.getcwd() + '/results'
    results = {}
    dt_tests = False
    mkdir(results_directory)
    for job_id in jobs:
        # Retrieve job details
        job_details = connection.scheduler.job_details(job_id)
        if job_details['requested_device_type_id']:
            device_type = job_details['requested_device_type_id']
        if job_details['description']:
            job_name = job_details['description']
        result = jobs[job_id]['result']
        bundle = jobs[job_id]['bundle']
        # Retrieve the log file
        binary_job_file = connection.scheduler.job_output(job_id)
        # Parse LAVA messages out of log
        raw_job_file = str(binary_job_file)
        job_file = ''
        dt_test = None
        dt_test_result = None
        dt_tests_passed = None
        dt_tests_failed = None
        for line in raw_job_file.splitlines():
            if '<LAVA_DISPATCHER>' not in line:
                if len(line) != 0:
                    job_file += line + '\n'
            if '### dt-test ### end of selftest' in line:
                dt_tests = True
                regex = re.compile("(?P<test>\d+\*?)")
                dt_test_results = regex.findall(line)
                dt_tests_passed = dt_test_results[2]
                dt_tests_failed = dt_test_results[3]
                if int(dt_test_results[3]) > 0:
                    dt_test_result = 'FAIL'
                else:
                    dt_test_result = 'PASS'
        # Retrieve bundle
        if bundle is not None:
            json_bundle = connection.dashboard.get(bundle)
            bundle_data = json.loads(json_bundle['content'])
            bundle_attributes =  bundle_data['test_runs'][0]['attributes']
            boot_meta = {}
            kernel_defconfig = None
            kernel_version = None
            kernel_endian = None
            kernel_boot_time = None
            kernel_tree = None
            kernel_image = None
            kernel_addr = None
            initrd_addr = None
            dtb_addr = None
            dtb_append = None
            fastboot = None
            fastboot_cmd = None
            if in_bundle_attributes(bundle_attributes, 'kernel.defconfig'):
                kernel_defconfig = bundle_attributes['kernel.defconfig']
            if in_bundle_attributes(bundle_attributes, 'kernel.version'):
                kernel_version = bundle_attributes['kernel.version']
            if in_bundle_attributes(bundle_attributes, 'kernel.endian'):
                kernel_endian = bundle_attributes['kernel.endian']
            if in_bundle_attributes(bundle_attributes, 'platform.fastboot'):
                fastboot = bundle_attributes['platform.fastboot']
            if in_bundle_attributes(bundle_attributes, 'kernel-boot-time'):
                kernel_boot_time = bundle_attributes['kernel-boot-time']
            if in_bundle_attributes(bundle_attributes, 'kernel.tree'):
                kernel_tree = bundle_attributes['kernel.tree']
            if in_bundle_attributes(bundle_attributes, 'kernel-image'):
                kernel_image = bundle_attributes['kernel-image']
            if in_bundle_attributes(bundle_attributes, 'kernel-addr'):
                kernel_addr = bundle_attributes['kernel-addr']
            if in_bundle_attributes(bundle_attributes, 'initrd-addr'):
                initrd_addr = bundle_attributes['initrd-addr']
            if in_bundle_attributes(bundle_attributes, 'dtb-addr'):
                dtb_addr = bundle_attributes['dtb-addr']
            if in_bundle_attributes(bundle_attributes, 'dtb-append'):
                dtb_append = bundle_attributes['dtb-append']

        # Record the boot log and result
        # TODO: Will need to map device_types to dashboard device types
        if kernel_defconfig and device_type and result:
            print 'Creating boot log for %s' % device_type
            log = 'boot-%s.log' % device_type
            directory = os.path.join(results_directory, kernel_defconfig)
            ensure_dir(directory)
            write_file(job_file, log, directory)
            if kernel_boot_time is None:
                kernel_boot_time = '0.0'
            if results.has_key(kernel_defconfig):
                results[kernel_defconfig].append({'device_type': device_type, 'dt_test_result': dt_test_result, 'dt_tests_passed': dt_tests_passed, 'dt_tests_failed': dt_tests_failed, 'kernel_boot_time': kernel_boot_time, 'result': result})
            else:
                results[kernel_defconfig] = [{'device_type': device_type, 'dt_test_result': dt_test_result, 'dt_tests_passed': dt_tests_passed, 'dt_tests_failed': dt_tests_failed, 'kernel_boot_time': kernel_boot_time, 'result': result}]
            # Create JSON format boot metadata
            print 'Creating JSON format boot metadata'
            boot_meta['boot_log'] = log
            # TODO: Fix this
            boot_meta['boot_log_html'] = None
            boot_meta['boot_result'] = result
            boot_meta['boot_time'] = kernel_boot_time
            # TODO: Fix this
            boot_meta['boot_warnings'] = None
            # TODO: Fix this
            boot_meta['dtb'] = None
            boot_meta['dtb_addr'] = dtb_addr
            boot_meta['dtb_append'] = dtb_append
            boot_meta['dt_test'] = dt_test
            boot_meta['endian'] = kernel_endian
            boot_meta['fastboot'] = fastboot
            boot_meta['fastboot_cmds'] = fastboot_cmd
            # TODO: Fix this
            boot_meta['initrd'] = None
            boot_meta['initrd_addr'] = initrd_addr
            boot_meta['kernel_image'] = kernel_image
            boot_meta['loadaddr'] = kernel_addr
            json_file = 'boot-%s.json' % device_type
            write_json(json_file, directory, boot_meta)


    if results and kernel_tree and kernel_version:
        print 'Creating boot summary for %s' % kernel_version
        boot = '%s-boot-report.txt' % kernel_version
        passed = 0
        failed = 0
        for defconfig, results_list in results.items():
            for result in results_list:
                if result['result'] == 'PASS':
                    passed += 1
                else:
                    failed += 1
        total = passed + failed
        with open(os.path.join(results_directory, boot), 'a') as f:
            f.write('to : %s\n' % args.email)
            f.write('from : lava@armcloud.us\n')
            f.write('subject : %s boot: %s boots: %s passed, %s failed (%s)\n' % (kernel_tree,
                                                                                str(total),
                                                                                str(passed),
                                                                                str(failed),
                                                                                kernel_version))
            f.write('\n')
            f.write('Full Build Report: http://status.armcloud.us/build/%s/kernel/%s/\n' % (kernel_tree, kernel_version))
            f.write('Full Boot Report: http://status.armcloud.us/boot/all/job/%s/kernel/%s/\n' % (kernel_tree, kernel_version))
            f.write('\n')
            f.write('Total Duration: %.2f minutes\n' % (duration / 60))
            f.write('Tree/Branch: %s\n' % kernel_tree)
            f.write('Git Describe: %s\n' % kernel_version)
            first = True
            for defconfig, results_list in results.items():
                for result in results_list:
                    if result['result'] != 'PASS':
                        if first:
                            f.write('\n')
                            f.write('Failed Boot Tests:\n')
                            first = False
                        f.write('\n')
                        f.write(defconfig)
                        f.write('\n')
                        break
                for result in results_list:
                    if result['result'] != 'PASS':
                        f.write('    %s   %ss   boot-test: %s\n' % (result['device_type'],
                                                                    result['kernel_boot_time'],
                                                                    result['result']))
                        f.write('    http://storage.armcloud.us/kernel-ci/%s/%s/%s/boot-%s.html' % (kernel_tree,
                                                                                                    kernel_version,
                                                                                                    defconfig,
                                                                                                    result['device_type']))
                        f.write('\n')
            f.write('\n')
            f.write('Full Boot Report:\n')
            for defconfig, results_list in results.items():
                f.write('\n')
                f.write(defconfig)
                f.write('\n')
                for result in results_list:
                    f.write('    %s   %ss   boot-test: %s\n' % (result['device_type'], result['kernel_boot_time'], result['result']))

    # dt-self-test
    if results and kernel_tree and kernel_version and dt_tests:
        print 'Creating device tree self test summary for %s' % kernel_version
        dt_self_test = '%s-dt-self-test-report.txt' % kernel_version
        passed = 0
        failed = 0
        for defconfig, results_list in results.items():
            for result in results_list:
                if result['dt_test_result'] == 'PASS':
                    passed += 1
                elif result['dt_test_result'] == 'FAIL':
                    failed += 1
        total = passed + failed
        with open(os.path.join(results_directory, dt_self_test), 'a') as f:
            f.write('to : %s\n' % args.email)
            f.write('from : lava@armcloud.us\n')
            f.write('subject : %s dt-self-test: %s tests: %s passed, %s failed (%s)\n' % (kernel_tree,
                                                                                str(total),
                                                                                str(passed),
                                                                                str(failed),
                                                                                kernel_version))
            f.write('\n')
            f.write('Full Test Report: http://status.armcloud.us/test/%s/kernel/%s/\n' % (kernel_tree, kernel_version))
            f.write('Full Build Report: http://status.armcloud.us/build/%s/kernel/%s/\n' % (kernel_tree, kernel_version))
            f.write('Full Boot Report: http://status.armcloud.us/boot/all/job/%s/kernel/%s/\n' % (kernel_tree, kernel_version))
            f.write('\n')
            f.write('Tree/Branch: %s\n' % kernel_tree)
            f.write('Git Describe: %s\n' % kernel_version)
            first = True
            for defconfig, results_list in results.items():
                for result in results_list:
                    if result['dt_test_result'] == 'FAIL':
                        if first:
                            f.write('\n')
                            f.write('Failed Device Tree Self Tests:\n')
                            first = False
                        f.write('\n')
                        f.write(defconfig)
                        f.write('\n')
                        break
                for result in results_list:
                    if result['dt_test_result'] == "FAIL":
                        f.write('    %s   %s/%s   dt-self-test: %s\n' % (result['device_type'],
                                                                         result['dt_tests_passed'],
                                                                         result['dt_tests_failed'],
                                                                         result['dt_test_result']))
                        f.write('    http://storage.armcloud.us/kernel-ci/%s/%s/%s/boot-%s.html' % (kernel_tree,
                                                                                                    kernel_version,
                                                                                                    defconfig,
                                                                                                    result['device_type']))
                        f.write('\n')
            f.write('\n')
            f.write('Full Device Tree Test Report:\n')
            for defconfig, results_list in results.items():
                first = True
                for result in results_list:
                    if result['dt_test_result']:
                        if first:
                            f.write('\n')
                            f.write(defconfig)
                            f.write('\n')
                            first = False
                        f.write('    %s   %s / %s   dt-self-test: %s\n' % (result['device_type'],
                                                                    result['dt_tests_passed'],
                                                                    result['dt_tests_failed'],
                                                                    result['dt_test_result']))

    # sendmail
    if args.email:
        print 'Sending e-mail summary to %s' % args.email
        cmd = 'cat %s | sendmail -t' % os.path.join(results_directory, boot)
        subprocess.check_output(cmd, shell=True)
        if dt_tests:
            cmd = 'cat %s | sendmail -t' % os.path.join(results_directory, dt_self_test)
            subprocess.check_output(cmd, shell=True)

def main(args):
    if args.boot:
        boot_report(args)
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--boot", help="creates a kernel-ci boot report from a given json file")
    parser.add_argument("--email", help="email address to send report to")
    args = parser.parse_args()
    main(args)
