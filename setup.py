import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="do-pod-dns-controller",
    version="0.1.2",
    author="Sean Lynch",
    author_email="seanl@literati.org",
    description="Controller for exposing pod nodeIPs via DNS on DigitalOcean.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seanlynch/do-pod-dns-controller",
    packages=["do_pod_dns_controller"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        "python-digitalocean",
        "kubernetes",
    ],
    entry_points={
        "console_scripts": [
            "do-pod-dns-controller = do_pod_dns_controller.controller:main"
        ]
    },
)
