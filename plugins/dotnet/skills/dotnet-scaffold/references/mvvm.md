# 按需 MVVM

仅明确选择 MVVM 时应用。WPF 默认使用核实过的稳定版 `CommunityToolkit.Mvvm`，标准布局将包纳入 CPM。不要额外加入 DI 容器、导航框架或 UI 组件库，除非所选能力需要。

在一个应用项目内建立 `Views/MainWindow.xaml`（含 code-behind）与 `ViewModels/MainWindowViewModel.cs`。同步修改：

1. `App.xaml` 的 StartupUri 为 `Views/MainWindow.xaml`，或明确使用单一启动方式；不能同时留下 StartupUri 与手动 Show 造成双窗口。
2. XAML `x:Class` 与 code-behind 的类/命名空间一致。
3. 给窗口配置正确 DataContext；普通单窗口可直接创建 ViewModel，无需为了注入而加入 Host。
4. 最少绑定一个真实展示属性，例如应用名称，验证启动与绑定，不虚构业务动作。

最小 ViewModel 形态（将命名空间和标题替换为实际项目值）：

```csharp
using CommunityToolkit.Mvvm.ComponentModel;

namespace MyApp.Desktop.ViewModels;

public sealed class MainWindowViewModel : ObservableObject
{
    private string title = "MyApp";

    public string Title
    {
        get => title;
        set => SetProperty(ref title, value);
    }
}
```

窗口 Title 或 TextBlock.Text 使用 `{Binding Title}`。只有真实动作才添加 RelayCommand/AsyncRelayCommand；需要属性生成器时检查 partial 声明、语言版本和对应包规则，不机械复制不兼容示例。

Models、Services、Converters、资源字典仅随真实内容出现。不默认拆多个程序集。MAUI 的页面/绑定遵循 MAUI 模板生命周期，不复制 WPF 的 StartupUri；WinForms 保留设计器支持，不机械套 WPF XAML 组织。

验证：编译、窗口启动、绑定呈现；条件允许时测试属性变化通知。无法访问桌面时分开报告编译通过和 UI 未验证。

参考：[ObservableObject](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/observableobject)。
