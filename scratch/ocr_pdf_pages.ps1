[CmdletBinding()]
param()

[Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null

$thLang = [Windows.Globalization.Language]::new('th')
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($thLang)
if ($null -eq $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}
Write-Host "OCR Engine Language: $($engine.RecognizerLanguage.LanguageTag)"

function AwaitTask($asyncOp) {
    return [System.Windows.Media.Ocr.OcrEngine].Assembly.GetType('System.WindowsRuntimeSystemExtensions')
}

$folder = 'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch_pdf_pages'
$outFile = 'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch_pdf_pages\ocr_results.txt'

if (Test-Path $outFile) { Remove-Item $outFile }

$files = Get-ChildItem $folder -Filter '*.png' | Sort-Object Name

foreach ($file in $files) {
    try {
        $sFile = [Windows.Storage.StorageFile]::GetFileFromPathAsync($file.FullName).GetAwaiter().GetResult()
        $stream = $sFile.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
        $decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetAwaiter().GetResult()
        $bmp = $decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult()
        $result = $engine.RecognizeAsync($bmp).GetAwaiter().GetResult()
        
        $header = "`n========================================`n=== $($file.Name) ===`n========================================`n"
        Add-Content -Path $outFile -Value $header -Encoding UTF8
        Add-Content -Path $outFile -Value $result.Text -Encoding UTF8
        Write-Host "Processed $($file.Name)"
    } catch {
        Write-Host "Error processing $($file.Name): $_"
    }
}
Write-Host "OCR process finished. Results saved to $outFile"
