#!/usr/bin/env python3
"""Exercise documented recipes with a real SDK in fresh temporary directories.

Not a project generator and not a model-selection test. Retains artifacts/logs.
Default: offline SDK fixtures. --online adds NuGet-dependent recipes.
"""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "plugins/dotnet/skills/dotnet-scaffold"
ASSETS = SKILL / "assets/config"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def xml_save(root, path):
    ET.indent(root, space="  ")
    write(path, ET.tostring(root, encoding="unicode") + "\n")


class Recipes:
    def __init__(self, online):
        self.root = Path(tempfile.mkdtemp(prefix="dotnet-scaffold-check-"))
        self.env = dict(os.environ, DOTNET_CLI_HOME=str(self.root / "cli"),
                        NUGET_PACKAGES=str(self.root / "packages"),
                        DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1", DOTNET_CLI_TELEMETRY_OPTOUT="1",
                        DOTNET_NOLOGO="1", DOTNET_ADD_GLOBAL_TOOLS_TO_PATH="0",
                        DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE="true")
        self.online = online
        self.sdk = self.run(self.root, "--version").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", self.sdk):
            raise RuntimeError(f"Expected stable SDK, got {self.sdk!r}")
        self.tfm = f"net{self.sdk.split('.')[0]}.0"
        # Isolated harness configuration: never copied into generated product defaults.
        source = '<add key="nuget.org" value="https://api.nuget.org/v3/index.json" />' if online else ""
        write(self.root / "NuGet.Config", f'<configuration><packageSources><clear />{source}</packageSources></configuration>')
        self.results = []

    def run(self, cwd, *args, timeout=120):
        result = subprocess.run(["dotnet", *map(str, args)], cwd=cwd, env=self.env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        with (self.root / "commands.log").open("a", encoding="utf-8") as log:
            log.write(f"\n{cwd}> dotnet {' '.join(map(str, args))}\n{result.stdout}{result.stderr}")
        if result.returncode:
            raise RuntimeError(f"dotnet {' '.join(map(str, args))}\n{result.stdout[-2200:]}{result.stderr[-700:]}")
        return result.stdout

    def standard(self, name):
        root = self.root / name
        root.mkdir()
        write(root / "global.json", (ASSETS / "global.json.template").read_text().replace("{{SDK_VERSION}}", self.sdk))
        for source, target in (("Directory.Build.props.template", "Directory.Build.props"), ("editorconfig.template", ".editorconfig")):
            shutil.copyfile(ASSETS / source, root / target)
        assert self.run(root, "--version").strip() == self.sdk
        self.run(root, "new", "sln", "-n", name)
        return root

    def project(self, root, template, name, rel=None, extra=()):
        out = root / (rel or f"src/{name}")
        self.run(root, "new", template, "-n", name, "-o", out, "--no-restore", *extra)
        return out / f"{name}.csproj"

    def solution(self, root):
        return next(p for p in root.iterdir() if p.suffix in (".sln", ".slnx"))

    def build(self, root, target):
        self.run(root, "restore", target, "-p:NuGetAudit=false", "--configfile", self.root / "NuGet.Config")
        self.run(root, "build", target, "--no-restore", "-c", "Release")

    def cpm(self, root):
        # Fixture transformation only: reject expressions/conditions, tested separately below.
        versions = {}
        trees = []
        for project in root.rglob("*.csproj"):
            tree = ET.parse(project).getroot()
            for ref in tree.findall(".//PackageReference"):
                version = ref.get("Version")
                if version is None:
                    continue
                if "$" in version or ref.get("Condition"):
                    raise ValueError("Fixture requires a dedicated conditional/expression recipe")
                name = ref.attrib["Include"]
                if name in versions and versions[name] != version:
                    raise ValueError(f"Conflicting fixture versions for {name}")
                versions[name] = version
                del ref.attrib["Version"]
            trees.append((tree, project))
        if versions:
            central = ET.parse(ASSETS / "Directory.Packages.props.template").getroot()
            group = ET.SubElement(central, "ItemGroup")
            for name, version in sorted(versions.items()):
                ET.SubElement(group, "PackageVersion", Include=name, Version=version)
            for tree, project in trees:
                xml_save(tree, project)
            xml_save(central, root / "Directory.Packages.props")

    @contextmanager
    def server(self, project):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        dll = project.parent / "bin/Release" / self.tfm / f"{project.stem}.dll"
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with (project.parent / "run.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(["dotnet", str(dll), "--urls", url], cwd=project.parent,
                                       env=self.env, stdout=log, stderr=log, creationflags=flags)
            try:
                deadline = time.monotonic() + 25
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Server exited; inspect run.log")
                    try:
                        with urllib.request.urlopen(url + "/health", timeout=1) as response:
                            assert response.status == 200
                        break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.2)
                else:
                    raise RuntimeError("Server did not become healthy")
                yield url
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def health(self, project):
        write(project.parent / "Program.cs", 'var builder = WebApplication.CreateBuilder(args);\nbuilder.Services.AddHealthChecks();\nvar app = builder.Build();\napp.MapHealthChecks("/health");\napp.Run();\n')

    def raw(self):
        root = self.root / "Raw"
        project = self.project(self.root, "console", "Raw", "Raw")
        assert not any((root / p).exists() for p in ("src", "global.json", "Directory.Build.props", "Directory.Packages.props"))
        self.build(root, project)
        assert "Hello, World!" in self.run(root, "run", "--project", project, "--no-build", "-c", "Release")

    def library(self):
        root = self.standard("Simple")
        project = self.project(root, "classlib", "Simple")
        self.run(root, "sln", self.solution(root), "add", project)
        assert len(list(root.rglob("*.csproj"))) == 1
        assert not (root / "Directory.Packages.props").exists()
        self.build(root, self.solution(root))
        self.run(root, "format", self.solution(root), "--no-restore")
        self.run(root, "format", self.solution(root), "--verify-no-changes", "--no-restore")

    def wpf(self):
        root = self.standard("Desktop")
        project = self.project(root, "wpf", "Desktop")
        self.build(root, project)
        assert not ET.parse(project).findall(".//PackageReference")

    def services(self):
        root = self.standard("Services")
        projects = []
        for name in ("Alpha", "Beta"):
            project = self.project(root, "webapi", name, f"services/{name}/src/{name}", ("--no-openapi",))
            self.health(project)
            assert not ET.parse(project).findall(".//ProjectReference")
            self.run(root, "sln", self.solution(root), "add", project)
            self.build(root, project)
            self.run(root, "publish", project, "--no-restore", "-c", "Release", "-o", self.root / "published" / name)
            projects.append(project)
        with self.server(projects[0]) as first, self.server(projects[1]) as second:
            assert first != second

    def conditional_cpm(self):
        root = self.standard("Conditional")
        feed = root / "feed"
        feed.mkdir()
        for version in ("1.0.0", "2.0.0"):
            with zipfile.ZipFile(feed / f"Fixture.Dependency.{version}.nupkg", "w") as package:
                package.writestr("Fixture.Dependency.nuspec", f'<package><metadata><id>Fixture.Dependency</id><version>{version}</version><authors>fixture</authors><description>Local validation fixture</description></metadata></package>')
                package.writestr("lib/netstandard2.1/_._", "")
        project = self.project(root, "classlib", "Conditional")
        (project.parent / "Class1.cs").unlink()
        tree = ET.parse(project).getroot()
        group = tree.find("PropertyGroup")
        group.remove(group.find("TargetFramework"))
        ET.SubElement(group, "TargetFrameworks").text = f"{self.tfm};netstandard2.1"
        ET.SubElement(group, "LangVersion").text = "12.0"
        ET.SubElement(group, "FixtureModernVersion").text = "2.0.0"
        refs = ET.SubElement(tree, "ItemGroup")
        ET.SubElement(refs, "PackageReference", Include="Fixture.Dependency", Version="1.0.0", Condition="'$(TargetFramework)' == 'netstandard2.1'", PrivateAssets="all")
        ET.SubElement(refs, "PackageReference", Include="Fixture.Dependency", Version="$(FixtureModernVersion)", Condition=f"'$(TargetFramework)' == '{self.tfm}'", PrivateAssets="all")
        xml_save(tree, project)
        def restore_versions():
            self.run(root, "restore", project, "--source", feed, "--configfile", self.root / "NuGet.Config", "-p:NuGetAudit=false")
            assets = json.loads((project.parent / "obj/project.assets.json").read_text())
            return {tfm: sorted(items) for tfm, items in assets["targets"].items()}
        before = restore_versions()
        # Move the property before the item that uses it; preserve both item conditions/metadata.
        central = ET.parse(ASSETS / "Directory.Packages.props.template").getroot()
        ET.SubElement(central.find("PropertyGroup"), "FixtureModernVersion").text = "2.0.0"
        group.remove(group.find("FixtureModernVersion"))
        versions = ET.SubElement(central, "ItemGroup")
        for ref in refs:
            ET.SubElement(versions, "PackageVersion", Include=ref.get("Include"), Version=ref.attrib.pop("Version"), Condition=ref.get("Condition"))
            assert ref.get("PrivateAssets") == "all"
        xml_save(tree, project)
        xml_save(central, root / "Directory.Packages.props")
        after = restore_versions()
        assert before == after
        assert before[self.tfm] == ["Fixture.Dependency/2.0.0"]
        assert before["netstandard2.1"] == ["Fixture.Dependency/1.0.0"]
        self.run(root, "build", project, "--no-restore", "-c", "Release")

    def clean(self):
        root = self.standard("Clean")
        projects = {name: self.project(root, "classlib", f"Clean.{name}") for name in ("Domain", "Application", "Infrastructure")}
        projects["Api"] = self.project(root, "webapi", "Clean.Api", extra=("--no-openapi",))
        graph = {"Domain": [], "Application": ["Domain"], "Infrastructure": ["Application"], "Api": ["Application", "Infrastructure"]}
        for name, dependencies in graph.items():
            project = projects[name]
            self.run(root, "sln", self.solution(root), "add", project)
            for dependency in dependencies:
                self.run(root, "add", project, "reference", projects[dependency])
            if name in ("Application", "Infrastructure"):
                tree = ET.parse(project).getroot()
                ET.SubElement(ET.SubElement(tree, "ItemGroup"), "PackageReference", Include="Microsoft.Extensions.DependencyInjection.Abstractions", Version="10.0.0")
                xml_save(tree, project)
                write(project.parent / "DependencyInjection.cs", f'using Microsoft.Extensions.DependencyInjection;\nnamespace Clean.{name};\npublic static class DependencyInjection\n{{\n    public static IServiceCollection Add{name}(this IServiceCollection services) => services;\n}}\n')
            class1 = project.parent / "Class1.cs"
            if class1.exists():
                class1.unlink()
            actual = {Path(ref.get("Include").replace("\\", "/")).stem.split(".")[-1] for ref in ET.parse(project).findall(".//ProjectReference")}
            assert actual == set(dependencies)
        self.health(projects["Api"])
        program = projects["Api"].parent / "Program.cs"
        write(program, "using Clean.Application;\nusing Clean.Infrastructure;\n" + program.read_text().replace("builder.Services.AddHealthChecks();", "builder.Services.AddApplication();\nbuilder.Services.AddInfrastructure();\nbuilder.Services.AddHealthChecks();"))
        self.cpm(root)
        self.build(root, self.solution(root))
        with self.server(projects["Api"]):
            pass

    def mvvm(self):
        root = self.standard("Mvvm")
        project = self.project(root, "wpf", "Mvvm.Desktop")
        tree = ET.parse(project).getroot()
        ET.SubElement(ET.SubElement(tree, "ItemGroup"), "PackageReference", Include="CommunityToolkit.Mvvm", Version="8.4.2")
        xml_save(tree, project)
        app = project.parent / "App.xaml"
        write(app, app.read_text(encoding="utf-8-sig").replace('StartupUri="MainWindow.xaml"', 'StartupUri="Views/MainWindow.xaml"'))
        for filename in ("MainWindow.xaml", "MainWindow.xaml.cs"):
            source = project.parent / filename
            destination = project.parent / "Views" / filename
            text = source.read_text(encoding="utf-8-sig").replace("Mvvm.Desktop.MainWindow", "Mvvm.Desktop.Views.MainWindow").replace("namespace Mvvm.Desktop", "namespace Mvvm.Desktop.Views")
            if filename.endswith(".cs"):
                text = text.replace("InitializeComponent();", "InitializeComponent();\n            DataContext = new Mvvm.Desktop.ViewModels.MainWindowViewModel();")
            else:
                text = text.replace('Title="MainWindow"', 'Title="{Binding Title}"')
            write(destination, text)
            source.unlink()
        write(project.parent / "ViewModels/MainWindowViewModel.cs", 'using CommunityToolkit.Mvvm.ComponentModel;\nnamespace Mvvm.Desktop.ViewModels;\npublic sealed class MainWindowViewModel : ObservableObject\n{\n    private string title = "Mvvm";\n    public string Title { get => title; set => SetProperty(ref title, value); }\n}\n')
        self.cpm(root)
        self.build(root, project)

        # Load the WPF XAML and exercise binding on an STA thread without showing a window.
        probe = self.project(root, "console", "MvvmProbe", "tests/MvvmProbe")
        probe_tree = ET.parse(probe).getroot()
        probe_group = probe_tree.find("PropertyGroup")
        probe_group.find("TargetFramework").text = ET.parse(project).findtext(".//TargetFramework")
        ET.SubElement(probe_group, "UseWPF").text = "true"
        xml_save(probe_tree, probe)
        self.run(root, "add", probe, "reference", project)
        write(probe.parent / "Program.cs", '''using System.Windows;
using System.Windows.Data;
using Mvvm.Desktop.ViewModels;
using Mvvm.Desktop.Views;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        var application = new Mvvm.Desktop.App();
        // Drain initial application startup before assigning the generated StartupUri.
        // This test exercises XAML/binding without displaying a window.
        application.ShutdownMode = ShutdownMode.OnExplicitShutdown;
        application.Dispatcher.Invoke(System.Windows.Threading.DispatcherPriority.ContextIdle, new Action(() => { }));
        application.InitializeComponent();
        if (application.StartupUri?.OriginalString != "Views/MainWindow.xaml")
            throw new InvalidOperationException("Incorrect StartupUri");
        var window = new MainWindow();
        var viewModel = (MainWindowViewModel)window.DataContext;
        var binding = BindingOperations.GetBindingExpression(window, Window.TitleProperty)
            ?? throw new InvalidOperationException("Missing Title binding");
        binding.UpdateTarget();
        window.Dispatcher.Invoke(System.Windows.Threading.DispatcherPriority.ContextIdle, new Action(() => { }));
        if (window.Title != "Mvvm") throw new InvalidOperationException($"Initial binding failed: {window.Title}");
        var changed = false;
        viewModel.PropertyChanged += (_, args) => changed |= args.PropertyName == "Title";
        viewModel.Title = "Updated";
        binding.UpdateTarget();
        window.Dispatcher.Invoke(System.Windows.Threading.DispatcherPriority.ContextIdle, new Action(() => { }));
        if (!changed || window.Title != "Updated") throw new InvalidOperationException("Property update failed");
        window.Close();
        application.Shutdown();
        Console.WriteLine("WPF XAML and binding passed; no window displayed.");
    }
}
''')
        self.build(root, probe)
        assert "WPF XAML and binding passed" in self.run(root, "run", "--project", probe, "--no-build", "-c", "Release")

    def blazor(self):
        root = self.standard("Blazor")
        self.project(root, "blazor", "BlazorApp", extra=("--interactivity", "Auto"))
        projects = list(root.rglob("*.csproj"))
        assert len(projects) == 2 and any(p.stem.endswith(".Client") for p in projects)
        self.run(root, "sln", self.solution(root), "add", *projects)
        self.cpm(root)
        self.build(root, self.solution(root))

    def execute(self, selected=None):
        cases = [("raw-console", self.raw), ("simple-library-and-format", self.library),
                 ("independent-services-build-run-publish", self.services), ("conditional-cpm", self.conditional_cpm)]
        if os.name == "nt":
            cases.append(("wpf-build", self.wpf))
        if self.online:
            cases.extend([("clean-api-cpm-build-run", self.clean), ("blazor-auto-build", self.blazor)])
            if os.name == "nt":
                cases.append(("wpf-mvvm-cpm-build-binding", self.mvvm))
        if selected:
            known = {name for name, _ in cases}
            if set(selected) - known:
                raise ValueError(f"Unavailable cases: {set(selected) - known}")
            cases = [(name, case) for name, case in cases if name in selected]
        print(f"Artifacts: {self.root}\nSDK: {self.sdk}", flush=True)
        for name, case in cases:
            try:
                case()
                result = {"case": name, "status": "PASS"}
            except Exception as error:
                result = {"case": name, "status": "FAIL", "detail": str(error)}
            self.results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        report = {"sdk": self.sdk, "online": self.online, "artifacts": str(self.root), "results": self.results,
                  "not_verified": ["agent selection and reference loading", "host installation/discovery", "WPF visible UI interaction", "MAUI", "k6 runtime", "containers", "CI", "DDD business modeling"]}
        write(self.root / "results.json", json.dumps(report, ensure_ascii=False, indent=2))
        return int(any(r["status"] != "PASS" for r in self.results))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Enable actual NuGet restores; requires network access")
    parser.add_argument("--case", action="append", help="Run only the named case; repeat to select several")
    args = parser.parse_args()
    raise SystemExit(Recipes(args.online).execute(args.case))
