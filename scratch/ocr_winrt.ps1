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

function Wait-WinRTAsync($asyncOp) {
    while ($asyncOp.Status -eq 0) {
        Start-Sleep -Milliseconds 20
    }
    if ($asyncOp.Status -eq 1) {
        return $asyncOp.GetResults()
    } else {
        throw "Async operation failed with status: $($asyncOp.Status)"
    }
}

$folder = 'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch_pdf_pages'
$outFile = 'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch_pdf_pages\ocr_results.txt'

if (Test-Path $outFile) { Remove-Item $outFile }

$files = Get-ChildItem $folder -Filter '*.png' | Sort-Object Name

foreach ($file in $files) {
    try {
        $sFile = Wait-WinRTAsync ([Windows.Storage.StorageFile]::GetFileFromPathAsync($file.FullName))
        $stream = Wait-WinRTAsync ($sFile.OpenAsync([Windows.Storage.FileAccessMode]::Read))
        $decoder = Wait-WinRTAsync ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream))
        $bmp = Wait-WinRTAsync ($decoder.GetSoftwareBitmapAsync())
        $result = Wait-WinRTAsync ($engine.RecognizeAsync($bmp))
        
        $header = "`n========================================`n=== $($file.Name) ===`n========================================`n"
        Add-Content -Path $outFile -Value $header -Encoding UTF8
        Add-Content -Path $outFile -Value $result.Text -Encoding UTF8
        Write-Host "Successfully processed $($file.Name)"
    } catch {
        Write-Host "Error processing $($file.Name): $_"
    }
}
Write-Host "OCR process finished. Results saved to $outFile"
