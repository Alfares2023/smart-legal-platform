from datetime import datetime
import os
import pathlib
import re
import subprocess

import cyclopts

from y2._console import console
from y2._tempdirs import mkdtemp


app = cyclopts.App(
    name="xcode",
    help="Manage Xcode project.",
)


_PBXPROJ = "project.pbxproj"


@app.command
def bump(
    xcode_project: pathlib.Path | None = None,
    store_version: bool = False,
    store_version_bump_year: bool = False,
):
    """Bump app versions."""
    if xcode_project:
        pbxproj = xcode_project / _PBXPROJ
    else:
        for f in pathlib.Path.cwd().iterdir():
            if f.suffix == ".xcodeproj":
                pbxproj = f / _PBXPROJ
                break
        else:
            console.fatal("Cannot find an Xcode project in the current directory.")
    if not pbxproj.exists():
        console.fatal(f"Xcode project not found: {pbxproj!s}")

    content = pbxproj.read_text()
    builds = re.findall(r"\n\s+VERSION_BUILD = (\d+);\s*\n", content)
    stores = re.findall(r"\n\s+VERSION_STORE = (\d+)\.(\d+);\s*\n", content)
    if len(builds) != 2:
        console.fatal(f"No build version: {builds}")
    if len(set(builds)) != 1:
        console.fatal(f"Inconsistent build version: {builds}")
    if len(stores) != 2:
        console.fatal(f"No store version: {stores}")
    if len(set(stores)) != 1:
        console.fatal(f"Inconsistent store version: {stores}")
    next_build = int(builds[0]) + 1
    content = re.sub(
        r"(\n\s+VERSION_BUILD = )(\d+)(;\s*\n)", rf"\g<1>{next_build}\g<3>", content
    )
    if store_version:
        if store_version_bump_year:
            next_store_year = int(stores[0][0]) + 1
            current_year = datetime.now().year
            if next_store_year < current_year:
                next_store_year = current_year
            next_store = f"{next_store_year}.1"
        else:
            next_store_minor = int(stores[0][1]) + 1
            next_store = f"{stores[0][0]}.{next_store_minor}"
        content = re.sub(
            r"(\n\s+VERSION_STORE = )(\d+\.\d+)(;\s*\n)",
            rf"\g<1>{next_store}\g<3>",
            content,
        )
    pbxproj.write_text(content)


@app.command
def build_and_upload(project_dir: pathlib.Path | None = None):
    """Build and upload the project using fastlane."""
    if project_dir:
        project_dir = project_dir.absolute()
    else:
        project_dir = pathlib.Path.cwd()

    if not (project_dir / "fastlane" / "Gymfile").exists():
        console.fatal(
            "Missing the fastlane/Gymfile file. (Run `fastlane gym init` to initialize.)"
        )

    depot_dir = project_dir.absolute()
    if not (depot_dir / ".git").exists():
        depot_dir = depot_dir.parent

    tmp_dir = mkdtemp(prefix="build.")
    console.print(f"Copying {depot_dir!s} to {tmp_dir!s}")
    work_dir = tmp_dir / depot_dir.name / project_dir.relative_to(depot_dir)
    subprocess.check_call(["cp", "-r", depot_dir, tmp_dir])
    env = os.environ.copy()
    env["FASTLANE_XCODEBUILD_SETTINGS_TIMEOUT"] = "120"
    subprocess.check_call(
        ["bundle", "exec", "fastlane", "build_and_upload"], env=env, cwd=work_dir
    )
