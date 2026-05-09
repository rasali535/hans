
$ip = "129.212.189.214"
$ports = 20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 2222, 3306, 3389, 5432, 8000, 8001, 8080, 8888, 15005
foreach ($port in $ports) {
    $t = New-Object Net.Sockets.TcpClient
    $c = $t.ConnectAsync($ip, $port)
    if ($c.Wait(300)) {
        Write-Host "Port $port is OPEN"
    } else {
        # Write-Host "Port $port is CLOSED"
    }
    $t.Close()
}
