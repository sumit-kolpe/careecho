param([string]$OutputDirectory = "data/audio")
# Windows-only fixture generation. No microphone or real patient recordings.
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$destination = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDirectory))
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$text = Get-Content -LiteralPath "data/sample_transcript.txt" -Raw
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synth.Rate = -1
    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $synth.SetOutputToWaveFile((Join-Path $destination "teachback.wav"), $format)
    $synth.Speak($text)
    $metadata = @{generator="Windows System.Speech"; voice=$synth.Voice.Name; sample_rate=16000; synthetic=$true; source="data/sample_transcript.txt"}
    $metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destination "provenance.json") -Encoding UTF8
} finally {
    $synth.Dispose()
}
