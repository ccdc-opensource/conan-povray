import glob
import os
import stat

from conans import ConanFile, AutoToolsBuildEnvironment, VisualStudioBuildEnvironment, tools, RunEnvironment

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

    def requirements(self):
        self.requires("boost/1.73.0")
        self.requires("zlib/1.2.11")
        self.requires("libpng/1.6.37")
        self.requires("libjpeg/9d")
        self.requires("libtiff/4.1.0")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def build(self):
        if self.settings.compiler == "Visual Studio":
            self._build_msvc()
        else:
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
        args = "DISTRIBUTION_MESSAGE_2=CCDC"
        with tools.chdir(self._source_subfolder):
            with tools.vcvars(self.settings):
                with tools.environment_append(VisualStudioBuildEnvironment(self).vars):
                    self.run("nmake -f makefile.vc {}".format(args))

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
            self.copy("*", src='bin', dst="bin")
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
