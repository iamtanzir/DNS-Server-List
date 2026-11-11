# Kahf Guard — Windows 10/11 DNS + DoH
# Run in an elevated PowerShell:
#   powershell -ExecutionPolicy Bypass -File windows-dns.ps1
$ErrorActionPreference = 'Stop'
$primary = '142.132.207.231'
$secondary = '157.90.95.113'
$doh = 'https://medium.kahfguard.com/dns-query'

Write-Host "Setting DNS to $primary / $secondary ..."
Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
    Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses @($primary, $secondary)
}

# DoH templates require Windows 11 22H2+ / Windows Server 2022.
try {
    Add-DnsClientDohServerAddress -ServerAddress $primary -DohTemplate $doh -AllowFallbackToUdp $false -AutoUpgrade $true -ErrorAction Stop
    Write-Host "DoH enabled for $primary"
} catch {
    Write-Host 'This Windows build has no DoH cmdlet; DNS is set but not encrypted.'
    Write-Host 'Use Windows 11 22H2+ or set DoH in the browser.'
}

ipconfig /flushdns | Out-Null
Write-Host 'Done. Verify with: Resolve-DnsName example.com'
