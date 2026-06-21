using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using WacliDesktop.Helpers;
using WacliDesktop.Services;
using WacliDesktop.Views;

namespace WacliDesktop;

public partial class HomeWindow : Window
{
    private readonly AppServices _app = AppServices.Instance;

    public HomeWindow()
    {
        InitializeComponent();
        _app.StatusChanged += UpdateStatus;
        Loaded += (_, _) =>
        {
            _app.StartBackgroundServices();
            UpdateStatus();
        };
        Closed += (_, _) =>
        {
            _app.StatusChanged -= UpdateStatus;
            _app.Modules.CloseAll();
            _app.Dispose();
        };
    }

    private void UpdateStatus()
    {
        StatusText.Text = _app.AuthStatusText;

        var authed = _app.AuthStatusText == "已登录";
        var disconnected = _app.AuthStatusText == "链接断开";
        StatusDot.Fill = authed
            ? new SolidColorBrush(Color.FromRgb(0x52, 0xc4, 0x1a))
            : new SolidColorBrush(Color.FromRgb(0xe2, 0x4b, 0x4a));

        if (disconnected)
            StatusText.Text = "链接断开";
    }

    private void ModuleTile_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn || btn.Tag is not string key) return;

        switch (key)
        {
            case "login":
                _app.Modules.Open(key, () => new ModuleShellWindow("登录配对", new LoginView(), 920, 580));
                break;
            case "browse":
                _app.Modules.Open(key, () => new ModuleShellWindow("数据浏览", new BrowseView(), 960, 620));
                break;
            case "sql":
                _app.Modules.Open(key, () => new ModuleShellWindow("SQLite 查询", new SqlView(), 980, 620));
                break;
            case "console":
                _app.Modules.Open(key, () => new ModuleShellWindow("命令工具", new ConsoleView(), 920, 640));
                break;
            case "toolbox":
                _app.Modules.Open(key, () => new ModuleShellWindow("赤瞳工具箱", new ChitungToolboxView(), 1080, 720));
                break;
            case "web":
                _app.Modules.Open(key, () => new ModuleShellWindow("赤瞳网页版", new ChitungWebView(), 1320, 860));
                break;
        }
    }

    private void BtnEnvSetup_Click(object sender, RoutedEventArgs e)
    {
        var win = new SetupProgressWindow { Owner = this };
        win.ShowDialog();
    }

    private void BtnYaoyaoFactory_Click(object sender, RoutedEventArgs e)
    {
        var win = new YaoyaoFactoryWindow { Owner = this };
        win.ShowDialog();
    }

    private void BtnHelp_Click(object sender, RoutedEventArgs e)
    {
        var win = new HelpWindow { Owner = this };
        win.ShowDialog();
    }
}
