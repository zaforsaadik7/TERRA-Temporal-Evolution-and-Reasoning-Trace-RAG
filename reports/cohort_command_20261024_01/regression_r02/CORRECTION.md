# System-directory binding correction

Self-review after initial 704-test PASS found the environment directory was
checked against powershell.exe's parent. On a real Windows installation this
is System32/WindowsPowerShell/v1.0, not System32. Changed comparison to the
pinned kernel32.dll directory. Added a synthetic nested-PowerShell-path test.
No real paths inspected. Initial package preserved; its two live-source rows
are superseded by this R02 package. Original final snapshots remain immutable.
