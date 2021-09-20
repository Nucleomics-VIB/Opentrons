<?php
 chdir('/var/www/cgi-bin/OT2MakeProtocol');
 $testdata="OT2inject_data.zip";
 header("Content-type: application/zip");
 header("Content-Disposition: attachment; filename = $testdata");
 header("Pragma: no-cache");
 header("Expires: 0");
 readfile("$testdata");
?>

header("Location: http://10.112.84.39/cgi-bin/OT2MakeProtocol/OT2MakeProtocol.php");
