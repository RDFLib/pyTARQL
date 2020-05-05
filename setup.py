"""Configure dependencies, license, etc."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytarql",
    version="0.5.0",
    author="Boris Pelakh",
    author_email="boris.pelakh@semanticarts.com",
    description="pyTARQL transforms CSV data to RDF using CONSTRUCT query",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/semanticarts/ontology-toolkit",
    packages=setuptools.find_packages(),
    install_requires=[
        'rdflib>=5.0.0',
        'requests'
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "pytarql = pytarql.pytarql:run"
        ]
    },
    python_requires='>=3.6',
)
