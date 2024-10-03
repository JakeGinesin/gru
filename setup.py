# setup.py

from setuptools import setup, find_packages

setup(
    name='gru',  # Replace with your desired package name
    version='0.1.0',
    description='A toolset for refining property-based tests using mutation analysis and LLMs.',
    author='Jake Ginesin',
    author_email='ginesin.j@northeastern.edu',
    url='https://github.com/JakeGinesin/gru',  # Replace with your repository URL
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'openai>=0.0.0',           # Specify the required version
        'pytest>=6.0.0',
        'pytest-json-report>=1.2.4',
        'hypothesis>=6.0.0',
        'astor',
        'requests'
        # Include other dependencies if any
    ],
    entry_points={
        'console_scripts': [
            #'tighten-pbt=gru.refine_pbts:tighten_repo_pbt',
            #'generalize-pbt=gru.refine_pbts:generalize_repo_pbt',
            'tighten-pbt=gru.refine_pbts:main',
            'generalize-pbt=gru.refine_pbts:main',
            #'analyze-pbts=gru.analyze_pbts:analyze_pbts_in_repo',
            'analyze-pbts=gru.analyze_pbts:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Adjust if using a different license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
