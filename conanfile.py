import glob
import os
import stat

from conans import ConanFile, AutoToolsBuildEnvironment, MSBuild, tools, RunEnvironment

class PovrayConan(ConanFile):
    name = "povray"
    version = "3.7.0.8"
    description = "The Persistence of Vision Raytracer."
    license = ["AGPL-3.0-only"]
    topics = ("conan", "freexl", "excel", "xls")
    homepage = "https://www.povray.org"
    url = "https://github.com/POV-Ray/povray"
    settings = "os_build", "arch_build", "compiler"

    _autotools= None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def configure(self):
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    # def build_requirements(self):
    #     if self.settings.os == "Windows" and self.settings.compiler != "Visual Studio" and \
    #        "CONAN_BASH_PATH" not in os.environ and tools.os_info.detect_windows_subsystem() != "msys2":
    #         self.build_requires("msys2/20190524")

    def build_requirements(self):
        self.build_requires("boost/1.73.0")
        self.build_requires("zlib/1.2.11")
        self.build_requires("libpng/1.6.37")
        self.build_requires("libjpeg/9d")
        self.build_requires("libtiff/4.1.0")
        if self.settings.os_build == 'Windows':
            self.build_requires('7zip/19.00')

    def source(self):
        if self.settings.os_build == "Windows":
            archive_name='povray-3.7.0.0.7z'
            # Building on windows Is a royal pain... I'll just grab a build
            tools.download(
                url=f'https://artifactory.ccdc.cam.ac.uk:443/artifactory/ccdc-3rdparty-windows-runtime-exes/{archive_name}',
                filename=archive_name,
                sha256='9fe7dead0e07e2425ff8c6784e6a6991c9a0feee2582563c6fa1450b37da8702',
                headers={
                'X-JFrog-Art-Api': os.environ.get("ARTIFACTORY_API_KEY", None)
            })
            self.run('7z x %s' % archive_name)
            os.unlink(archive_name)
            os.rename('povray-3.7.0.0', self._source_subfolder)
        else:
            tools.get(**self.conan_data["sources"][self.version])
            os.rename(self.name + "-" + self.version, self._source_subfolder)
        # tools.replace_in_file(os.path.join(self._source_subfolder, 'source', 'backend','povray.h'),
        #     "#error Please complete the following DISTRIBUTION_MESSAGE_2 definition", "")
        # tools.replace_in_file(os.path.join(self._source_subfolder, 'source', 'backend','povray.h'),
        #     "FILL IN NAME HERE.........................", "CCDC")
        # tools.rmdir(os.path.join(self._source_subfolder, 'libraries'))

    def build(self):
        if self.settings.compiler == "Visual Studio":
            pass
            # self._build_msvc()
        else:
            self._build_autotools()

    def _build_autotools(self):
        with tools.environment_append(RunEnvironment(self).vars):
            with tools.chdir(os.path.join(self._source_subfolder, 'unix')):
                prebuild_script = "./prebuild.sh"
                st = os.stat(prebuild_script)
                os.chmod(prebuild_script, st.st_mode | stat.S_IEXEC)
                self.run(prebuild_script)
            try:
                autotools = self._configure_autotools()
                autotools.make()
            except:
                self.output.info(open('config.log', errors='backslashreplace').read())
                raise

    def _build_msvc(self):
        # args = "DISTRIBUTION_MESSAGE_2=CCDC"
        msbuild = MSBuild(self)
        # msbuild.build_env.include_paths.append("mycustom/directory/to/headers")
        # msbuild.build_env.lib_paths.append("mycustom/directory/to/libs")
        # msbuild.build_env.link_flags = []

        msbuild.build(
            project_file=os.path.join(self._source_subfolder, "windows", "vs10", "povray.sln"),
            build_type='Release',
            arch='x86_64',
        )

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        args = [
            'COMPILED_BY=CCDC',
            f'--with-boost-libdir={tools.unix_path(self.deps_cpp_info["boost"].lib_paths[0])}'
        ]

        self._autotools.configure(args=args, configure_dir=self._source_subfolder)
        return self._autotools

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        if self.settings.os_build == "Windows":
            self.copy("*", src=self._source_subfolder)
        else:
            autotools = self._configure_autotools()
            autotools.install()
            # tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
            # for la_file in glob.glob(os.path.join(self.package_folder, "lib", "*.la")):
            #     os.remove(la_file)

    def package_info(self):
        bin_path = os.path.join(self.package_folder, 'bin')
        self.output.info('Appending PATH environment variable: %s' % bin_path)
        self.env_info.PATH.append(bin_path)
