from setuptools import setup, find_packages

PACKAGE_NAME = 'static-deployer'
PACKAGE_VER = '0.1.0'
PACKAGE_DESC = 'Deploy static websites using a single command'
PACKAGE_URL = 'https://github.com/jweyrich/static-deployer'
PACKAGE_LICENSE = 'BSD-3-Clause'
PACKAGE_AUTHOR = 'Jardel Weyrich'
PACKAGE_AUTHOR_EMAIL = 'jweyrich@gmail.com'

if __name__ == "__main__":
    setup(
        name=PACKAGE_NAME,
        version=PACKAGE_VER,
        description=PACKAGE_DESC,
        url=PACKAGE_URL,
        author=PACKAGE_AUTHOR,
        author_email=PACKAGE_AUTHOR_EMAIL,
        license=PACKAGE_LICENSE,
        packages=find_packages(where='src'),
        package_dir={"": "src"},
        py_modules=['cli'],
        entry_points='''
            [console_scripts]
            static_deployer=cli:main
        ''',
        install_requires=[
            'attrs >=21.2.0,<22.0.0',
            'boto3 >=1.18.39,<2.0.0',
            'toml >=0.10.2,<1.0.0',
        ],
        python_requires='>=3.7, <4.0',
        classifiers=[
            'Development Status :: 1 - Planning',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: BSD License',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
        ],
    )
