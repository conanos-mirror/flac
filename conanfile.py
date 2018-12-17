#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
from conanos.build import config_scheme
import os


class FlacConan(ConanFile):
    name = "flac"
    version = "1.3.2"
    description = "Free Lossless Audio Codec"
    url = "https://github.com/conanos/flac"
    homepage = "https://github.com/xiph/flac"
    license = "BSD"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "use_asm": [True, False], "fPIC": [True, False]}
    default_options = "shared=True", "use_asm=True", "fPIC=True"
    requires = "libogg/1.3.3@conanos/stable"

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def build_requirements(self):
        if self.options.use_asm:
            self.build_requires("nasm/2.13.01@conanos/stable")

    def source(self):
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["CONAN_ARCH"] = str(self.settings.arch)
        cmake.definitions["USE_ASM"] = self.options.use_asm
        if self.settings.os != "Windows":
            cmake.definitions["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.fPIC
        cmake.configure()
        return cmake

    def build(self):
        cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        cmake = self.configure_cmake()
        cmake.install()
        self.copy(pattern="COPYING.*", dst="licenses", src=self._source_subfolder, keep_path=False)
        
        pc_content ='''
        prefix={prefix}
        exec_prefix=${{prefix}}
        libdir=${{prefix}}/lib
        toolexeclibdir=${{prefix}}/lib
        includedir=${{prefix}}/include
        
        Name: {name}
        Description: {description}
        Version: {version}
        Libs: -L${{toolexeclibdir}} -l{name}
        Cflags: -I${{includedir}}
        '''
        
        tools.save('%s/lib/pkgconfig/%s.pc'%(self.package_folder, self.name), 
        pc_content.format(prefix=self.package_folder, name=self.name, version=self.version, description=self.description))

        tools.save('%s/lib/pkgconfig/%s++.pc'%(self.package_folder, self.name), 
        pc_content.format(prefix=self.package_folder, name='%s++'%(self.name), version=self.version, description=self.description))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if not self.options.shared:
            self.cpp_info.defines = ["FLAC__NO_DLL"]
