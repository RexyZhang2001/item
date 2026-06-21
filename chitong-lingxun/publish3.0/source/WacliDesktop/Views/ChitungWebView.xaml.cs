using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;

namespace WacliDesktop.Views;

public partial class ChitungWebView : UserControl
{
    private readonly Uri? _localEntryUri;

    public ChitungWebView()
    {
        InitializeComponent();
        _localEntryUri = ResolveLocalEntryUri();
        Loaded += OnLoaded;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        if (_localEntryUri is null)
        {
            StatusText.Text = "未找到内置 Web 前端，请先运行 copy-chitung-web.ps1 复制 chitung-frontend/dist。";
            return;
        }

        try
        {
            await ChitungWeb.EnsureCoreWebView2Async();
            ChitungWeb.Source = _localEntryUri;
            StatusText.Text = $"已加载：{_localEntryUri.LocalPath}";
        }
        catch (Exception ex)
        {
            StatusText.Text = $"WebView2 初始化失败：{ex.Message}";
        }
    }

    private static Uri? ResolveLocalEntryUri()
    {
        var baseDir = AppContext.BaseDirectory;
        var candidates = new[]
        {
            Path.Combine(baseDir, "Assets", "ChitungWeb", "index.html"),
            Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "Assets", "ChitungWeb", "index.html"),
        };

        foreach (var candidate in candidates)
        {
            var fullPath = Path.GetFullPath(candidate);
            if (File.Exists(fullPath))
                return new Uri(fullPath);
        }
        return null;
    }

    private void BtnReload_Click(object sender, RoutedEventArgs e)
    {
        ChitungWeb.Reload();
    }

    private void BtnOpenExternal_Click(object sender, RoutedEventArgs e)
    {
        if (_localEntryUri is null)
            return;
        Process.Start(new ProcessStartInfo(_localEntryUri.AbsoluteUri) { UseShellExecute = true });
    }
}
