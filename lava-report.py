#!/usr/bin/python
# <variable> = required
# Usage ./lava-report.py <option> [json]
import argparse
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
        job_file = str(binary_job_file)
        # Retrieve bundle
        if bundle is not None:
            json_bundle = connection.dashboard.get(bundle)
            bundle_data = json.loads(json_bundle['content'])
            bundle_attributes =  bundle_data['test_runs'][0]['attributes']
            boot_meta = {}
            kernel_defconfig = None
            kernel_version = None
            kernel_boot_time = None
            kernel_tree = None
            kernel_image = None
            kernel_addr = None
            initrd_addr = None
            dtb_addr = None
            dtb_append = None
            if in_bundle_attributes(bundle_attributes, 'kernel.defconfig'):
                kernel_defconfig = bundle_attributes['kernel.defconfig']
            if in_bundle_attributes(bundle_attributes, 'kernel.version'):
                kernel_version = bundle_attributes['kernel.version']
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
        if kernel_defconfig and device_type and kernel_boot_time and result:
            print 'Creating boot log for %s' % device_type
            log = 'boot-%s.log' % device_type
            directory = os.path.join(results_directory, kernel_defconfig)
            mkdir(directory)
            write_file(job_file, log, directory)
            if results.has_key(kernel_defconfig):
                results[kernel_defconfig].append({'device_type': device_type, 'kernel_boot_time': kernel_boot_time, 'result': result})
            else:
                results[kernel_defconfig] = [{'device_type': device_type, 'kernel_boot_time': kernel_boot_time, 'result': result}]
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
            # TODO: Fix this
            boot_meta['endian'] = None
            # TODO: Fix this
            boot_meta['initrd'] = None
            boot_meta['initrd_addr'] = initrd_addr
            boot_meta['kernel_image'] = kernel_image
            boot_meta['loadaddr'] = kernel_addr
            json_file = 'boot-%s.json' % device_type
            write_json(json_file, directory, boot_meta)


    if results and kernel_tree and kernel_version:
        print 'Creating boot summary for %s' % kernel_version
        log = '%s-boot-report.log' % kernel_version
        with open(os.path.join(results_directory, log), 'a') as f:
            f.write('Status Dashboard: http://status.armcloud.us/boot/all/job/%s/kernel/%s/\n' % (kernel_tree, kernel_version))
            f.write('\n')
            f.write('Total duration: %.2f seconds\n' % duration)
            f.write('Tree/Branch: %s\n' % kernel_tree)
            f.write('Git describe: %s\n' % kernel_version)
            f.write('\n')
            f.write('Full Report:\n')
            for defconfig, results_list in results.items():
                f.write('\n')
                f.write(defconfig)
                f.write('\n')
                for result in results_list:
                    f.write('    %s   %ss   %s\n' % (result['device_type'], result['kernel_boot_time'], result['result']))
        if args.jenkins:
            print 'Creating jenkins boot summary for %s' % kernel_version
            log = 'env.properties'
            with open(os.path.join(results_directory, log), 'a') as f:
                f.write('SUMMARY=Status Dashboard: http://status.armcloud.us/boot/all/job/%s/kernel/%s/ \\\n' % (kernel_tree, kernel_version))
                f.write('\\\n')
                f.write('Total duration: %.2f seconds \\\n' % duration)
                f.write('Tree/Branch: %s \\\n' % kernel_tree)
                f.write('Git describe: %s \\\n' % kernel_version)
                f.write('\\\n')
                f.write('Full Report: \\\n')
                for defconfig, results_list in results.items():
                    f.write('\\\n')
                    f.write('%s \\\n' % defconfig)
                    for result in results_list:
                        f.write('    %s   %ss   %s \\\n' % (result['device_type'], result['kernel_boot_time'], result['result']))

def main(args):
    if args.boot:
        boot_report(args)
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--boot", help="creates a kernel-ci boot report from a given json file")
    parser.add_argument("--jenkins", action='store_true', help="create jenkins style env.properties summary")
    args = parser.parse_args()
    main(args)
