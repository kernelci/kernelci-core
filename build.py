#!/usr/bin/env python
#
# NOTES:
# - override ARCH and CROSS_COMPILE using environment variables
#
# TODO
#
import os
import sys
import subprocess
import getopt
import tempfile
import fnmatch
import shutil
import re
import stat
import json
import platform
import time
import requests
import ConfigParser
from urlparse import urljoin

cross_compilers = {
    "arm": "arm-linux-gnueabihf-",
    "arm64": "aarch64-linux-gnu-",
    "mips": "mips-linux-",
    "i386": None,
    "x86": None,
    "x86_64": None,
}

# Defaults
arch = "arm"
cross_compile = cross_compilers[arch]
git_describe = None
git_describe_v = None
git_commit = None
ccache = None
make_threads = 2
kbuild_output_prefix = 'build'
silent = True
build_target = None
build_log = None
build_log_f = None

def usage():
    print "Usage:", sys.argv[0], "[options] [make target]"
    
def do_post_retry(url=None, data=None, headers=None, files=None):
    retry = True
    while retry:
        try:
            response = requests.post(url, data=data, headers=headers, files=files)
            if str(response.status_code)[:1] != "2":
                raise Exception(response.content)
            else:
                return response.content
                retry = False
        except Exception as e:
            print "ERROR: failed to publish"
            print e
            time.sleep(10)

def do_make(target=None, log=False):
    make_args = ''
    make_args += "-j%d -k " %make_threads
    if silent:
        make_args += "-s "
    make_args += "ARCH=%s " %arch
    if cross_compile:
        make_args += "CROSS_COMPILE=%s " %cross_compile
    if ccache:
        prefix = ''
        if cross_compile:
            prefix = cross_compile
        make_args += 'CC="ccache %sgcc" ' %prefix
    if kbuild_output:
        make_args += "O=%s " %kbuild_output
    if target:
        make_args += target
    make_cmd = 'make %s' %make_args
    if target == "oldconfig":
        make_cmd = 'yes "" |' + make_cmd
    print make_cmd

    make_stdout = None
    if log:
        build_log_f.write("#\n# " + make_cmd + "\n#\n")
        make_stdout = build_log_f
    p1 = subprocess.Popen(make_cmd , shell=True,
                          stdout=make_stdout,
                          stderr=subprocess.STDOUT,
    )
#    p2 = subprocess.Popen("tee --append %s" %os.path.join(kbuild_output, "build.log"),
#                          shell=True,
#                          stdin=p1.stdout)
#    p2.communicate()
    p1.communicate()
    return p1.wait()

#
# cmdline args
#
defconfig = None
kconfig_tmpfile = None
kconfig_tmpfile_fd = None
kconfig_frag = None
frag_names = []
install = False
publish = False
url = None
token = None
job = None
boot_cmd = None
use_environment = False

# temp frag file: used to collect all kconfig fragments
kconfig_tmpfile_fd, kconfig_tmpfile = tempfile.mkstemp(prefix='kconfig-')

# ARCH
if os.environ.has_key('ARCH'):
    arch = os.environ['ARCH']
else:
    os.environ['ARCH'] = arch

try:
    opts, args = getopt.getopt(sys.argv[1:], "b:c:ip:se")

except getopt.GetoptError as err:
    print str(err) # will print something like "option -a not recognized"
    sys.exit(2)
for o, a in opts:
    if o == "-b":
        boot_cmd = a
        install = True
    if o == '-c':
        defs = a.split('+')
        for a in defs:
            if os.path.exists("arch/%s/configs/%s" % (arch, a)):
                defconfig = a
            elif a == "defconfig" or a == "tinyconfig" or re.match("all(\w*)config", a):
                defconfig = a
            elif os.path.exists(a):
                # Append fragment contents to temp frag file
                frag = open(a)
                os.write(kconfig_tmpfile_fd, "\n# fragment from: %s\n" %a)
                for line in frag:
                    os.write(kconfig_tmpfile_fd, line)
                frag.close()
                frag_names.append(os.path.basename(os.path.splitext(a)[0]))
            elif a.startswith("CONFIG_"):
                # add to temp frag file
                os.write(kconfig_tmpfile_fd, a + "\n")
                os.fsync(kconfig_tmpfile_fd)
                frag_names.append(a)
            else:
                print "ERROR: kconfig file/fragment (%s) doesn't exist" %a
                sys.exit(1)

    if o == '-i':
        install = True
    if o == '-p':
        config = ConfigParser.ConfigParser()
        try:
            config.read(os.path.expanduser('~/.buildpy.cfg'))
            url = config.get(a, 'url')
            token = config.get(a, 'token')
            publish = True
        except:
            print "ERROR: unable to load configuration file"
    if o == '-s':
        silent = not silent
    if o == '-e':
        print "Reading build variables from environment"
        url = os.environ['API']
        token = os.environ['TOKEN']
        publish = True
        use_environment = True

# Default umask for file creation
os.umask(022)

# Set number of make threads to number of local processors + 2
if os.path.exists('/proc/cpuinfo'):
    output = subprocess.check_output('grep -c processor /proc/cpuinfo',
                                     shell=True)
    make_threads = int(output) + 2

# CROSS_COMPILE
if cross_compilers.has_key(arch):
    cross_compile = cross_compilers[arch]
if os.environ.has_key('CROSS_COMPILE'):
    cross_compile = os.environ['CROSS_COMPILE']
else:
    if cross_compile:
        os.environ['CROSS_COMPILE'] = cross_compile

# KBUILD_OUTPUT
kbuild_output = kbuild_output_prefix
if arch:
    kbuild_output += "-%s" % arch
if os.environ.has_key('KBUILD_OUTPUT'):
    kbuild_output = os.environ['KBUILD_OUTPUT']
else:
    os.environ['KBUILD_OUTPUT'] = kbuild_output
if not os.path.exists(kbuild_output):
    os.makedirs(kbuild_output)
build_log = os.path.join(kbuild_output, "build.log")
build_log_f = open(build_log, 'w', 0)

# ccache
ccache = None
ccache_dir = None
if not os.environ.has_key('CCACHE_DISABLE'):
    ccache = subprocess.check_output('which ccache | cat', shell=True).strip()
if ccache and len(ccache):
    if os.environ.has_key('CCACHE_DIR'):
        ccache_dir = os.environ['CCACHE_DIR']
    else:
        ccache_dir = os.path.join(os.getcwd(), '.ccache' + '-' + arch)
        #ccache_dir = os.path.join(os.getcwd(), '.ccache')
        os.environ['CCACHE_DIR'] = ccache_dir
else:
    ccache_dir = None

# Gather info from environment variables
if use_environment:
    if os.environ.has_key('GIT_DESCRIBE'):
        git_describe = os.environ['GIT_DESCRIBE']
    if os.environ.has_key('GIT_DESCRIBE_VERBOSE'):
        git_describe_v = os.environ['GIT_DESCRIBE_VERBOSE']
    if os.environ.has_key('BRANCH'):
        git_branch = os.environ['BRANCH']
    if os.environ.has_key('COMMIT_ID'):
        git_commit = os.environ['COMMIT_ID']
    if os.environ.has_key('TREE'):
        git_url = os.environ['TREE']
else:
    # Gather info from .git
    if os.path.exists('.git'):
        git_commit = subprocess.check_output('git log -n1 --format=%H', shell=True).strip()
        git_url = subprocess.check_output('git config --get remote.origin.url |cat', shell=True).strip()
        git_branch = subprocess.check_output('git rev-parse --abbrev-ref HEAD', shell=True).strip()
        git_describe_v = subprocess.check_output('git describe --match=v[234]\*', shell=True).strip()
        git_describe = subprocess.check_output('git describe', shell=True).strip()
    else:
        print "Could not gather build information from environment or .git directory"
        exit(1)



cc_cmd = "gcc -v 2>&1"
if cross_compile:
    cc_cmd = "%sgcc -v 2>&1" %cross_compile
gcc_version = subprocess.check_output(cc_cmd, shell=True).splitlines()[-1]

start_time = time.time()

#
# Config
#
dot_config = os.path.join(kbuild_output, '.config')

if defconfig or frag_names:
    base = ""
    if defconfig:
        do_make(defconfig, log=True)
        base = dot_config

    if len(frag_names):
        kconfig_frag = os.path.join(kbuild_output, 'frag-' + '+'.join(frag_names) + '.config')
        shutil.copy(kconfig_tmpfile, kconfig_frag)
        os.chmod(kconfig_frag, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        if os.path.exists("scripts/kconfig/merge_config.sh"):
            cmd = "scripts/kconfig/merge_config.sh -O %s %s %s > /dev/null 2>&1" %(kbuild_output, base, kconfig_frag)
            print cmd
            subprocess.call(cmd, shell = True)
        else:
            print "ERROR: merge_config.sh no present, Trying old 'cat' way."
            cmd = "cat %s >> %s" %(kconfig_frag, dot_config)
            print cmd
            subprocess.call(cmd, shell = True)
            do_make("oldconfig", log=True)

elif os.path.exists(dot_config):
    print "Re-using .config:", dot_config
    defconfig = "existing"
else:
    print "ERROR: Missing kernel config"
    sys.exit(0)

# 
# Build kernel
#
if len(args) >= 1:
    build_target = args[0]
result = do_make(build_target, log=True)

# Build modules
modules = None
if result == 0:
    modules = not subprocess.call('grep -cq CONFIG_MODULES=y %s' %dot_config, shell=True) 
    if modules:
        result |= do_make('modules', log=True)

build_time = time.time() - start_time

# Install
bmeta = {}
if install:
    install_path = os.path.join(os.getcwd(), '_install_', git_describe)
    if defconfig:
        install_path = os.path.join(install_path, '-'.join([arch, defconfig]))
    if len(frag_names):
        install_path += '+' + '+'.join(frag_names)

    os.environ['INSTALL_PATH'] = install_path
    if not os.path.exists(install_path):
        os.makedirs(install_path)
    
    boot_dir = "%s/arch/%s/boot" %(kbuild_output, arch)

    text_offset = -1
    system_map = os.path.join(kbuild_output, "System.map")
    if os.path.exists(system_map):
        virt_text = subprocess.check_output('grep " _text" %s' %system_map, shell=True).split()[0]
        text_offset = int(virt_text, 16) & (1 << 30)-1  # phys: cap at 1G
        shutil.copy(system_map, install_path)
    else:
        system_map = None
        text_offset = None

    dot_config_installed = os.path.join(install_path, "kernel.config")
    shutil.copy(dot_config, dot_config_installed)

    shutil.copy(build_log, install_path)
    if kconfig_frag:
        shutil.copy(kconfig_frag, install_path)

    # Patterns for matching kernel images by architecture
    if arch == 'arm':
        patterns = ['zImage', 'xipImage']
    elif arch == 'arm64':
        patterns = ['Image']
    # TODO: Fix this assumption. ARCH != ARM* == x86
    else:
        patterns = ['bzImage']

    kimage_file = None
    kimages = []
    for pattern in patterns:
        for root, dirnames, filenames in os.walk(boot_dir):
            for filename in fnmatch.filter(filenames, pattern):
                kimages.append(os.path.join(root, filename))
                shutil.copy(os.path.join(root, filename), install_path)

    vmlinux_file = os.path.join(kbuild_output, "vmlinux")
    if os.path.isfile(vmlinux_file):
        import elf
        bmeta.update(elf.read(vmlinux_file))
        bmeta["vmlinux_file_size"] = os.stat(vmlinux_file).st_size

    if len(kimages) == 1:
        kimage_file = kimages[0]
    elif len(kimages) > 1:
        for kimage in kimages:
            if os.path.basename(kimage).startswith('z'):
                kimage_file = kimage

    dtb_dest = None
    for root, dirnames, filenames in os.walk(os.path.join(boot_dir, 'dts')):
        for filename in fnmatch.filter(filenames, '*.dtb'):
            # Found a dtb
            dtb = os.path.join(root, filename)
            dtb_dest = os.path.join(install_path, 'dtbs')
            # Check if the dtb exists in a subdirectory
            if root.split(os.path.sep)[-1] != 'dts':
                dest = os.path.join(install_path, 'dtbs',
                                        root.split(os.path.sep)[-1])
            else:
                dest = os.path.join(install_path, 'dtbs')
            if not os.path.exists(dest):
                os.makedirs(dest)
            # Copy the dtb
            shutil.copy(dtb, dest)

    #do_make('install')
    if modules:
        tmp_mod_dir = tempfile.mkdtemp()
        os.environ['INSTALL_MOD_PATH'] = tmp_mod_dir
        os.environ['INSTALL_MOD_STRIP'] = "1"
        os.environ['STRIP'] = "%sstrip" %cross_compile
        do_make('modules_install')
        modules_tarball = "modules.tar.xz"
        cmd = "(cd %s; tar -Jcf %s lib/modules)" %(tmp_mod_dir, modules_tarball)
        subprocess.call(cmd, shell=True)
        shutil.copy(os.path.join(tmp_mod_dir, modules_tarball), install_path)
        shutil.rmtree(tmp_mod_dir)

    bmeta["build_time"] = round(build_time, 2)
    if result == 0:
        bmeta['build_result'] = "PASS"
    else:
        bmeta['build_result'] = "FAIL"

    if boot_cmd:
        cmd = "(cd %s; %s)" % (install_path, boot_cmd)
        print "Running: %s" % cmd
        subprocess.call(cmd, shell=True)
        
    bmeta['arch'] = "%s" %arch
    bmeta["cross_compile"] = "%s" %cross_compile
    bmeta["compiler_version"] = "%s" %gcc_version
    bmeta["git_url"] = "%s" %git_url
    bmeta["git_branch"] =  "%s" %git_branch
    bmeta["git_describe"] =  "%s" %git_describe
    bmeta["git_describe_v"] =  "%s" %git_describe_v
    bmeta["git_commit"] = "%s" %git_commit
    bmeta["defconfig"] = "%s" %defconfig
    if len(frag_names):
        defconfig_full = defconfig
        defconfig_full += '+' + '+'.join(frag_names)
        bmeta["defconfig_full"] = defconfig_full

    if kconfig_frag:
        bmeta["kconfig_fragments"] = "%s" %os.path.basename(kconfig_frag)
    else:
        bmeta["kconfig_fragments"] = None

    if kimage_file:
        bmeta["kernel_image"] = "%s" %os.path.basename(kimage_file)
    else:
        bmeta["kernel_image"] = None
    
    bmeta["kernel_config"] = "%s" %os.path.basename(dot_config_installed)
    if system_map:
        bmeta["system_map"] = "%s" %os.path.basename(system_map)
    else:
        bmeta["system_map"] = None

    if text_offset:
        bmeta["text_offset"] = "0x%08x" %text_offset
    else:
        bmeta["text_offset"] = None

    if dtb_dest:
        bmeta["dtb_dir"] = "%s" %os.path.basename(dtb_dest)
    else:
        bmeta["dtb_dir"] = None

    if modules and modules_tarball:
        bmeta["modules"] = "%s" %modules_tarball
    else:
        bmeta["modules"] = None

    bmeta["build_log"] = "%s" %os.path.basename(build_log)
    bmeta["build_platform"] = platform.uname()

    if "TREE_NAME" in os.environ and len(os.environ["TREE_NAME"]) > 0:
        job = os.environ["TREE_NAME"]
        bmeta["job"] = job
    else:
        if publish:
            print "ERROR: TREE_NAME not set, aborting publish step"
            publish = False

    # Create JSON format build metadata
    build_json = os.path.join(install_path, 'build.json')
    build_json_f = open(build_json, 'w')
    json.dump(bmeta, build_json_f, indent=4, sort_keys=True)
    build_json_f.close()

    if publish and job:
        artifacts = []
        headers = {}
        upload_data = {}
        build_data = {}
        if "defconfig_full" in bmeta:
            defconfig = defconfig_full
        publish_path = os.path.join(job, git_branch, git_describe, arch, defconfig)
        headers['Authorization'] = token
        build_data['path'] = publish_path
        build_data['file_server_resource'] = publish_path
        build_data['job'] = job
        build_data['kernel'] = git_describe
        build_data['git_branch'] = git_branch
        build_data['defconfig'] = defconfig
        build_data['arch'] = arch
        if "defconfig_full" in bmeta:
            build_data['defconfig_full'] = defconfig_full
        count = 1
        for root, dirs, files in os.walk(install_path):
            if count == 1:
                top_dir = root
            for file_name in files:
                name = file_name
                if root != top_dir:
                    # Get the relative subdir path
                    subdir = root[len(top_dir)+1:]
                    name = os.path.join(subdir, file_name)
                artifacts.append(('file' + str(count),
                                  (name,
                                   open(os.path.join(root, file_name), 'rb'))))
                count += 1
        upload_url = urljoin(url, '/upload')
        build_url = urljoin(url, '/build')
        publish_response = do_post_retry(url=upload_url, data=build_data, headers=headers, files=artifacts)
        print "INFO: published artifacts"
        for publish_result in json.loads(publish_response)["result"]:
            print "%s/%s" % (publish_path, publish_result['filename'])
        print "INFO: triggering build"
        headers['Content-Type'] = 'application/json'
        do_post_retry(url=build_url, data=json.dumps(build_data), headers=headers)

#
# Cleanup
#
if kconfig_tmpfile:
    os.unlink(kconfig_tmpfile)

if result:
    subprocess.call("cat %s" %build_log, shell=True)
sys.exit(result)
