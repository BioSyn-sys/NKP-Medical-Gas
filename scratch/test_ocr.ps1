$winmdPath = "C:\Windows\System32\WinMetadata\Windows.Media.winmd"
$winmdStorage = "C:\Windows\System32\WinMetadata\Windows.Storage.winmd"
$winmdGraphics = "C:\Windows\System32\WinMetadata\Windows.Graphics.winmd"
$winmdGlob = "C:\Windows\System32\WinMetadata\Windows.Foundation.winmd"

$code = @"
using System;
using System.IO;
using System.Threading.Tasks;
using Windows.Globalization;
using Windows.Media.Ocr;
using Windows.Graphics.Imaging;
using Windows.Storage;

public class WinOcrHelper {
    public static async Task<string> RecognizeFile(string filePath) {
        StorageFile file = await StorageFile.GetFileFromPathAsync(filePath);
        using (var stream = await file.OpenAsync(FileAccessMode.Read)) {
            BitmapDecoder decoder = await BitmapDecoder.CreateAsync(stream);
            SoftwareBitmap bmp = await decoder.GetSoftwareBitmapAsync();
            OcrEngine engine = OcrEngine.TryCreateFromLanguage(new Language("th")) ?? OcrEngine.TryCreateFromUserProfileLanguages();
            OcrResult res = await engine.RecognizeAsync(bmp);
            return res.Text;
        }
    }
}
"@

try {
    Add-Type -TypeDefinition $code -ReferencedAssemblies "System.Runtime.WindowsRuntime.dll", $winmdPath, $winmdStorage, $winmdGraphics, $winmdGlob -Language CSharp
    Write-Host "Add-Type succeeded!"
} catch {
    Write-Host "Add-Type error: $_"
}
