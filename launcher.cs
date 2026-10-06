using System;
using System.Diagnostics;
using System.IO;

internal static class SiMarketLauncher
{
    private static string Quote(string value)
    {
        return "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
    }

    private static string FindPython(string appDirectory)
    {
        string[] candidates = {
            Path.Combine(appDirectory, "runtime", "python.exe"),
            Path.Combine(appDirectory, ".venv", "Scripts", "python.exe")
        };

        foreach (string candidate in candidates)
        {
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        string path = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (string directory in path.Split(Path.PathSeparator))
        {
            string candidate = Path.Combine(directory.Trim(), "python.exe");
            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        return null;
    }

    [STAThread]
    private static int Main()
    {
        string appDirectory = AppDomain.CurrentDomain.BaseDirectory;
        string appFile = Path.Combine(appDirectory, "app.py");
        string python = FindPython(appDirectory);

        if (!File.Exists(appFile))
        {
            Console.Error.WriteLine("app.py was not found. Extract the complete project or portable ZIP first.");
            Console.ReadKey();
            return 1;
        }

        if (python == null)
        {
            Console.Error.WriteLine("Python was not found. Extract the complete portable ZIP or install project dependencies first.");
            Console.ReadKey();
            return 1;
        }

        ProcessStartInfo startInfo = new ProcessStartInfo();
        startInfo.FileName = python;
        startInfo.Arguments =
            "-m streamlit run " + Quote(appFile) +
            " --server.address 127.0.0.1 --server.headless false";
        startInfo.WorkingDirectory = appDirectory;
        startInfo.UseShellExecute = false;
        startInfo.CreateNoWindow = false;

        try
        {
            Process.Start(startInfo);
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("Could not start Si Market助手: " + exception.Message);
            Console.ReadKey();
            return 1;
        }
    }
}
