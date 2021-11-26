import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Conupedia",
    version="1.0.0",
    author="Rani Rafid",
    author_email="rani.rafid@concordia.ca",
    description="Currently in development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ra-Ni/Conupedia",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "app"},
    packages=setuptools.find_packages(where="app"),
    python_requires=">=3.6",
)