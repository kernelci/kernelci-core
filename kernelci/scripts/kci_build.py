#!/usr/bin/env python3
#
# Copyright (C) 2018, 2019, 2020, 2021 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import sys
import os
import lzma as xz

from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from kernelci.legacy.cli import Args, Command, parse_opts  # noqa: E402
import kernelci  # noqa: E402
import kernelci.build  # noqa: E402
import kernelci.config  # noqa: E402
import kernelci.legacy  # noqa: E402
import kernelci.storage  # noqa: E402


class cmd_validate(Command):
    help = "Validate the YAML configuration"
    opt_args = [Args.verbose]

    def __call__(self, configs, args):
        # ToDo: Use jsonschema

        entries = [
            'trees', 'fragments', 'build_configs',
        ]
        err = kernelci.config.validate_yaml(args.yaml_config, entries)
        if err:
            print(err)
            return False

        return True


class cmd_list_configs(Command):
    help = "List the build configurations"

    def __call__(self, configs, args):
        for conf_name in list(configs['build_configs'].keys()):
            print(conf_name)
        return True


class cmd_tree_branch(Command):
    help = "Print the name of the tree and branch for a given build config"
    args = [Args.build_config]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        print(conf.tree.name)
        print(conf.tree.url)
        print(conf.branch)
        return True


class cmd_update_mirror(Command):
    help = "Update the local kernel git mirror"
    args = [Args.build_config, Args.mirror]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        kernelci.build.update_mirror(conf, args.mirror)
        return True


class cmd_update_repo(Command):
    help = "Update the local kernel repository checkout"
    args = [Args.build_config, Args.kdir]
    opt_args = [Args.mirror]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        kernelci.build.update_repo(conf, args.kdir, args.mirror)
        return True


class cmd_describe(Command):
    help = "Print the git commit, describe and verbose describe from kdir"
    args = [Args.build_config, Args.kdir]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        commit = kernelci.build.head_commit(args.kdir)
        describe = kernelci.build.git_describe(conf.tree.name, args.kdir)
        verbose = kernelci.build.git_describe_verbose(args.kdir)
        print(commit)
        print(describe)
        print(verbose or describe)
        return True


class cmd_generate_fragments(Command):
    help = "Generate the config fragment files in kdir"
    args = [Args.build_config, Args.kdir]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        kernelci.build.generate_fragments(conf, args.kdir)
        return True


class cmd_generate_defconfig_fragments(Command):
    help = "Generate the config fragment files for a given defconfig"
    args = [Args.defconfig, Args.kdir]

    def __call__(self, configs, args):
        fragments = configs['fragments']
        split = args.defconfig.split('+')
        defconfig = split.pop(0)
        for part in split:
            frag = fragments.get(part)
            if frag and frag.configs:
                kernelci.build.generate_config_fragment(frag, args.kdir)
        return True


class cmd_expand_fragments(Command):
    help = "Expand a defconfig string with full fragment paths"
    args = [Args.defconfig]

    def __call__(self, configs, args):
        frags = configs['fragments']
        split = args.defconfig.split('+')
        expanded = [split.pop(0)]
        for part in split:
            frag = frags.get(part)
            if frag:
                expanded.append(frag.path)
            else:
                expanded.append(part)
        print('+'.join(expanded))
        return True


class cmd_list_variants(Command):
    help = "Print the list of build variants for a given build configuration"
    args = [Args.build_config]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        for variant in conf.variants:
            print(variant.name)
        return True


class cmd_arch_list(Command):
    help = "Print the list of CPU architecture names for a given build variant"
    args = [Args.build_config, Args.variant]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        variant = conf.get_variant(args.variant)
        for arch in variant.arch_list:
            print(arch)
        return True


def _show_build_env(build_env, arch=None):
    print(build_env.name)
    print(build_env.cc)
    print(build_env.cc_version)
    if arch:
        print(build_env.get_arch_param(arch, 'name') or arch)
        for param in 'cross_compile', 'cross_compile_compat':
            print(build_env.get_arch_param(arch, param) or '')


class cmd_get_build_env(Command):
    help = "Print the build environment parameters for a given build variant"
    args = [Args.build_config, Args.variant]
    opt_args = [Args.arch]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        variant = conf.get_variant(args.variant)
        _show_build_env(variant.build_environment, args.arch)
        return True


class cmd_get_reference(Command):
    help = "Print reference tree and branch for bisections"
    args = [Args.tree_name, Args.branch]

    def __call__(self, configs, args):
        for conf in configs['build_configs'].values():
            if conf.tree.name == args.tree_name and conf.branch == args.branch:
                if conf.reference:
                    print(conf.reference.tree.url)
                    print(conf.reference.tree.name)
                    print(conf.reference.branch)
                    return True
        return False


class cmd_show_build_env(Command):
    help = "Show parameters of a given build environment"
    args = [Args.build_env]
    opt_args = [Args.arch]

    def __call__(self, configs, args):
        build_env = configs['build_environments'][args.build_env]
        _show_build_env(build_env, args.arch)
        return True


class cmd_list_kernel_configs(Command):
    help = "List the kernel configs to build for a given build configuration"
    args = [Args.build_config, Args.kdir]
    opt_args = [Args.variant, Args.arch]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        configs = kernelci.build.list_kernel_configs(
            conf, args.kdir, args.variant, args.arch)
        for item in configs:
            print(' '.join(item))
        return True


class cmd_init_bmeta(Command):
    help = "Create initial bmeta.json"
    args = [Args.kdir]
    opt_args = [Args.output, Args.build_config, Args.install,
                Args.tree_name, Args.tree_url, Args.branch,
                Args.commit, Args.describe, Args.describe_verbose,
                Args.build_env, Args.arch]

    def __call__(self, configs, args):
        if args.build_config:
            conf = configs['build_configs'][args.build_config]
            tree_name = conf.tree.name
            tree_url = conf.tree.url
            branch = conf.branch
        else:
            tree_name = args.tree_name
            tree_url = args.tree_url
            branch = args.branch
        if not all((tree_name, tree_url, branch)):
            print("""\
Invalid arguments, either of these 2 sets are possible:
   --tree-name, --tree-url and --branch
or
   --build-config (the tree and branch are read from the YAML config)\
""")
            return False

        step = kernelci.build.RevisionData(args.kdir, args.output, reset=True)
        print("Initialising build meta-data in {}".format(step.output_path))
        res = step.run(opts={
            'tree': tree_name,
            'url': tree_url,
            'branch': branch,
            'commit': args.commit,
            'describe': args.describe,
            'describe_verbose': args.describe_verbose
        })

        if args.install:
            print("Install directory: {}".format(step.install_path))
            step.install()

        if res and (args.build_env or args.arch):
            if not (args.build_env and args.arch):
                print("""\
Invalid arguments, --build-env and --arch need to be used together.""")
                return False
            build_env = configs['build_environments'][args.build_env]
            step = kernelci.build.EnvironmentData(args.kdir, args.output)
            res = step.run(opts={'build_env': build_env, 'arch': args.arch})
            if args.install:
                step.install()

        return res


class MakeCommand(Command):
    args = [Args.kdir]
    opt_args = [Args.verbose, Args.output, Args.j, Args.log, Args.install]
    step_cls = None

    def __call__(self, configs, args):
        step = self._get_step(args)
        if not step.is_enabled():
            print("Not enabled, skipping.")
            return True
        opts = self._get_opts(args, configs)
        res = step.run(args.j, args.verbose, opts)
        if args.install:
            install_res = self._install_step(step, args)
            res = res and install_res
        return res

    def _get_step(self, args):
        if self.step_cls is None:
            raise ValueError("Step class not defined.")
        return self.step_cls(args.kdir, args.output, args.log)

    def _get_opts(self, args, configs):
        return dict()

    def _install_step(self, step, args):
        return step.install(args.verbose)


class cmd_make_config(MakeCommand):
    help = "Make kernel config"
    args = MakeCommand.args + [Args.defconfig]
    step_cls = kernelci.build.MakeConfig

    def _get_opts(self, args, configs):
        return {
            'defconfig': args.defconfig,
            'frags_config': configs['fragments'],
        }


class cmd_fetch_firmware(MakeCommand):
    help = "Fetch firmware"
    step_cls = kernelci.build.FetchFirmware


class cmd_make_kernel(MakeCommand):
    help = "Make a kernel image"
    step_cls = kernelci.build.MakeKernel


class cmd_make_modules(MakeCommand):
    help = "Build kernel modules"
    step_cls = kernelci.build.MakeModules

    def _install_step(self, step, args):
        return step.install(args.verbose, args.j)


class cmd_make_dtbs(MakeCommand):
    help = "Build device trees"
    step_cls = kernelci.build.MakeDeviceTrees


class cmd_make_kselftest(MakeCommand):
    help = "Build kselftest"
    step_cls = kernelci.build.MakeSelftests


class cmd_push_kernel(Command):
    help = "Push the kernel build artifacts"
    args = [Args.kdir, Args.storage_config]
    opt_args = [Args.storage_cred, Args.output]

    def _compress_gki_artifacts(self, install, meta):
        # gki_defconfig kernel builds are exceptional and generate hundreds of
        # megabytes in several files.  This requires compression to work around
        # upload limits with kernelci-backend.
        kernel_image_name = meta.get('bmeta', 'kernel', 'image')
        artifacts = ["logs/kernel.log"]
        artifacts.append('/'.join(["kernel", kernel_image_name]))
        for e in artifacts:
            source_filename = os.path.join(install, e)
            data = open(source_filename, 'rb').read()
            zf = xz.open(f'{source_filename}.xz', mode='wb',
                         format=xz.FORMAT_XZ, preset=9)
            zf.write(data)
            zf.close()
            os.unlink(source_filename)

    def _discover_files(self, path):
        artifacts = []
        for root, _, files in os.walk(path):
            for fname in files:
                px = os.path.relpath(root, path)
                artifacts.append(
                    (os.path.join(root, fname), os.path.join(px, fname))
                )
        return artifacts

    def __call__(self, configs, args):
        install = kernelci.build.Step.get_install_path(args.kdir, args.output)
        meta = kernelci.build.Metadata(install)

        defconfig = meta.get('bmeta', 'kernel', 'defconfig')
        if defconfig == "gki_defconfig":
            self._compress_gki_artifacts(install, meta)

        storage_conf = configs['storage_configs'][args.storage_config]
        storage = kernelci.storage.get_storage(storage_conf, args.storage_cred)
        artifacts = self._discover_files(install)
        publish_path = meta.get('bmeta', 'kernel', 'publish_path')
        print("Upload path: {}".format(publish_path))
        storage.upload_multiple(artifacts, publish_path)
        return True


class cmd_pull_tarball(Command):
    help = "Downloads and untars kernel sources"
    args = [Args.kdir, Args.url]
    opt_args = [Args.kernel_tarball, Args.retries, Args.delete]

    def __call__(self, configs, args):
        retries = args.retries or 1
        tarball = args.kernel_tarball or 'linux-src.tar.gz'
        return kernelci.build.pull_tarball(
            args.kdir, args.url, tarball, retries, args.delete)

# -----------------------------------------------------------------------------
# Legacy commands
#
# These commands don't follow the new API design with a separate storage, so
# they may use the kernelci-backend API to upload files directly.  Still they
# should be using the Storage configuration object to get the base URL rather
# than --storage which is now deprecated.


class cmd_check_new_commit(Command):
    help = "Check if a new commit is available on a branch"
    args = [Args.build_config, Args.storage_config]

    def __call__(self, configs, args):
        build_conf = configs['build_configs'][args.build_config]
        storage_conf = configs['storage_configs'][args.storage_config]
        storage_url = storage_conf.base_url
        update = kernelci.legacy.check_new_commit(build_conf, storage_url)
        if update is False or update is True:
            return update
        print(update)
        return True


class cmd_update_last_commit(Command):
    help = "Update the last commit file on the remote storage server"
    args = [Args.build_config, Args.api, Args.db_token, Args.commit]

    def __call__(self, configs, args):
        conf = configs['build_configs'][args.build_config]
        kernelci.legacy.set_last_commit(
            conf, args.api, args.db_token, args.commit)
        return True


class cmd_push_tarball(Command):
    help = "Create and up a source tarball to the remote storage server"
    args = [Args.build_config, Args.kdir, Args.storage_config,
            Args.api, Args.db_token]
    opt_args = [Args.db_config]  # This should become mandatory

    def __call__(self, configs, args):
        build_conf = configs['build_configs'][args.build_config]
        storage_conf = configs['storage_configs'][args.storage_config]
        func_args = (
            build_conf, args.kdir, storage_conf.base_url,
            args.api, args.db_token
        )
        if not all(func_args):
            print("Invalid arguments")
            return False
        tarball_url = kernelci.legacy.push_tarball(*func_args)
        if not tarball_url:
            return False
        print(tarball_url)
        return True


def main():
    opts = parse_opts("kci_build", globals())
    configs = kernelci.config.load(opts.get_yaml_configs())
    status = opts.command(configs, opts)
    sys.exit(0 if status is True else 1)


if __name__ == '__main__':
    main()
