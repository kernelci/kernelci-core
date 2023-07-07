class MakeXXXXXX(Step):

    @property
    def name(self):
        return 'XXXXXX'

    def build_and_install_OpenCSD(self):
    #cwd = os.getcwd()
    #os.chdir(kdir)

        repourl = 'https://github.com/Linaro/OpenCSD.git'
        clone_git(repourl, "/linux/tools/XXXXXX/OpenCSD", 'master')
        os.chdir("/linux/tools/XXXXXX/OpenCSD/decoder/build/linux")
        subprocess.run(["make", "clean"])
        subprocess.run(["make", "ARCH=arm64", "CROSS_COMPILE=/usr/bin/aarch64-linux-gnu-"])
        subprocess.run(["make", "install"])
        # Set LD_LIBRARY_PATH environment variable
        ld_library_path = '/linux/tools/XXXXXX/OpenCSD/decoder/lib/builddir'
        os.environ['LD_LIBRARY_PATH'] = ld_library_path
        # Set CSINCLUDES environment variable
        cs_includes = '/linux/tools/XXXXXX/OpenCSD/decoder/include/'
        os.environ['CSINCLUDES'] = cs_includes
        # Set CSLIBS environment variable
        cs_libs = '/linux/tools/XXXXXX/OpenCSD/decoder/lib/builddir/'
        os.environ['CSLIBS'] = cs_libs



    def build_and_install_XXXXXX(self):
        print("XXXXXX build")
        os.chdir("/linux")
        # Build XXXXXX with the system installed cross compiler
        XXXXXX_make_flags = "NO_LIBPERL=1 ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- VF=1 CORESIGHT=1 -C tools/XXXXXX"
        # Clean, build, and install XXXXXX
        subprocess.run(["make"] + XXXXXX_make_flags.split())
        tarball_name = "XXXXXXtool.tar.gz"
        source_dir = "/linux/tools/XXXXXX"
        make_tarball(source_dir, tarball_name)
        subprocess.run(["make", "clean"])


    def run(self, jopt=None, verbose=False, opts=None):
        """Make the XXXXXX


        """
        arch = self._meta.get('bmeta', 'environment', 'arch')
        cross_compile = self._meta.get('bmeta', 'environment', 'cross_compile')
        full_path = os.path.abspath(self._output_path)
        print(full_path)
        print(arch)
        print(cross_compile)
        self.build_and_install_OpenCSD()
        self.build_and_install_XXXXXX()