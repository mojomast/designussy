$sourcePath = "c:\Users\kyle\projects\bananajam\assets\static\elements"
$archivePath = "c:\Users\kyle\projects\bananajam\assets\static\elements\archive"

# Create archive folder if it doesn't exist
if (-not (Test-Path $archivePath)) {
    New-Item -ItemType Directory -Path $archivePath -Force | Out-Null
}

# Hash table to track unique files
$hashes = @{}
$movedCount = 0

# Get all files recursively (excluding archive folder)
$files = Get-ChildItem -Path $sourcePath -Recurse -File | Where-Object { $_.FullName -notlike "*\archive\*" }

Write-Host "Scanning $($files.Count) files for duplicates..."

foreach ($file in $files) {
    $hash = (Get-FileHash -Algorithm SHA256 -Path $file.FullName).Hash
    
    if ($hashes.ContainsKey($hash)) {
        # This is a duplicate, move it to archive
        Write-Host "Moving duplicate: $($file.Name)"
        Move-Item -LiteralPath $file.FullName -Destination $archivePath -Force
        $movedCount++
    } else {
        # First occurrence, add to hash table
        $hashes[$hash] = $file.FullName
    }
}

Write-Host "`nCleanup complete!"
Write-Host "Moved $movedCount duplicate files to archive folder."
Write-Host "Kept $($hashes.Count) unique files."
