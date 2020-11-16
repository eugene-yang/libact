#!/usr/bin/env python

from io import open # python 2 compatibility
import os
from os.path import join
from setuptools import setup, Extension
import sys

BUILD_HINTSVM = int(os.environ.get("LIBACT_BUILD_HINTSVM", 1))
BUILD_VARIANCE_REDUCTION = int(os.environ.get("LIBACT_BUILD_VARIANCE_REDUCTION", 1))


on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
# read the docs could not compile numpy and c extensions
if on_rtd:
    extensions = []
    cmdclasses = {}
    setup_requires = []
    install_requires = []
    tests_require = []
else:
    from Cython.Build import cythonize
    from Cython.Distutils import build_ext
    import numpy
    import numpy.distutils

    from numpy.distutils.system_info import get_info
    # from sklearn._build_utils.get_blas_info
    def get_blas_info():
        def atlas_not_found(blas_info_):
            def_macros = blas_info.get('define_macros', [])
            for x in def_macros:
                if x[0] == "NO_ATLAS_INFO":
                    # if x[1] != 1 we should have lapack
                    # how do we do that now?
                    return True
                if x[0] == "ATLAS_INFO":
                    if "None" in x[1]:
                        # this one turned up on FreeBSD
                        return True
            return False

        blas_info = get_info('blas_opt', 0)
        if (not blas_info) or atlas_not_found(blas_info):
            cblas_libs = ['cblas']
            blas_info.pop('libraries', None)
        else:
            cblas_libs = blas_info.pop('libraries', [])

        return cblas_libs, blas_info

    cblas_libs, blas_info = get_blas_info()
    cblas_includes = [join('src', 'cblas'),
                      numpy.get_include(),
                      *blas_info.pop('include_dirs', [])]

    if sys.platform == 'darwin':
        print("Platform Detection: Mac OS X. Link to openblas...")
        extra_link_args = []
        libraries = ['openblas']
        library_dirs = ['/opt/local/lib']
        # include_dirs = (numpy.distutils.misc_util.get_numpy_include_dirs() +
        #                 ['/opt/local/include'])
        include_dirs = cblas_includes + ['/opt/local/include']
    else:
        # assume linux otherwise, unless we support Windows in the future...
        print("Platform Detection: Linux. Link to liblapacke...")
        extra_link_args = ['-L/usr/lib -llapacke -llapack -lblas']
        include_dirs = cblas_includes + ['/opt/local/include']
        # include_dirs = (numpy.distutils.misc_util.get_numpy_include_dirs() +
        #                 ['/usr/include/'])
        libraries = ['lapacke', 'lapack', 'blas']
        library_dirs = ['/usr/lib']

    extensions = []
    if BUILD_VARIANCE_REDUCTION:
        print("Build VarianceReduction...")
        extensions.append(
            Extension(
                "libact.query_strategies._variance_reduction",
                ["libact/query_strategies/src/variance_reduction/variance_reduction.c"],
                extra_link_args=extra_link_args,
                extra_compile_args=['-std=c11'],
                include_dirs=include_dirs,
                libraries=libraries,
                library_dirs=library_dirs,
            )
        )
    if BUILD_HINTSVM:
        print("Build HintSVM...")
        extensions.append(
            Extension(
                "libact.query_strategies._hintsvm",
                sources=["libact/query_strategies/_hintsvm.pyx",
                         "libact/query_strategies/src/hintsvm/libsvm_helper.c",
                         "libact/query_strategies/src/hintsvm/svm.cpp"],
                include_dirs=[numpy.get_include(),
                              "libact/query_strategies/src/hintsvm/"],
                extra_compile_args=['-lstdc++'],
            )
        )

    extensions = cythonize(extensions)
    cmdclasses = {'build_ext': build_ext}
    setup_requires = []
    with open('./requirements.txt') as f:
        requirements = f.read().splitlines()
    install_requires = requirements
    tests_require = [
        'coverage',
    ]


setup(
    name='libact',
    version='0.1.6',
    description='Pool-based active learning in Python',
    long_description=open('README.md', 'r', newline='', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    author='Y.-Y. Yang, S.-C. Lee, Y.-A. Chung, T.-E. Wu, H.-T. Lin',
    author_email='b01902066@csie.ntu.edu.tw, b01902010@csie.ntu.edu.tw, '
        'b01902040@csie.ntu.edu.tw, r00942129@ntu.edu.tw, htlin@csie.ntu.edu.tw',
    url='https://github.com/ntucllab/libact',
    cmdclass=cmdclasses,
    setup_requires=setup_requires,
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    test_suite='libact',
    packages=[
        'libact',
        'libact.base',
        'libact.models',
        'libact.models.multilabel',
        'libact.labelers',
        'libact.query_strategies',
        'libact.query_strategies.multilabel',
        'libact.query_strategies.multiclass',
        'libact.utils',
    ],
    package_dir={
        'libact': 'libact',
        'libact.base': 'libact/base',
        'libact.models': 'libact/models',
        'libact.labelers': 'libact/labelers',
        'libact.query_strategies': 'libact/query_strategies',
        'libact.query_strategies.multiclass': 'libact/query_strategies/multiclass',
        'libact.utils': 'libact/utils',
    },
    ext_modules=extensions,
)
