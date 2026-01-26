from setuptools import find_packages, setup

package_name = "g1_nl_commands"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ros2_ws",
    maintainer_email="you@example.com",
    description="Natural-language command router for Unitree G1 (outputs task plans).",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "nl_command_router = g1_nl_commands.nl_command_router:main",
            "nl_command_tester = g1_nl_commands.nl_command_tester:main",
        ],
    },
)
