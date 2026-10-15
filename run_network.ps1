$port = 8000
$ip = (Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "169.254*" -and $_.IPAddress -ne "127.0.0.1" } | Select-Object -First 1 -ExpandProperty IPAddress)
if (-not $ip) { $ip = "<LAN-IP>" }
Write-Host "MESC Copilot: http://$ip`:$port"
Write-Host "Swagger API:  http://$ip`:$port/docs"
python -m uvicorn app:app --host 0.0.0.0 --port $port
