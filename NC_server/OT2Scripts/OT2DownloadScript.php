<?php
chdir('/var/www/cgi-bin/OT2uploads/');
$file = "NC_protocol.py";
header('Content-Description: File Transfer');
header('Content-Disposition: attachment; filename='.basename($file));
header('Expires: 0');
header('Cache-Control: must-revalidate');
header('Pragma: public');
header('Content-Length: ' . filesize($file));
header("Content-Type: text/plain");
readfile($file);
?>

<?php echo '<p><a href=http://10.112.84.39/webtools/Workflow.htm>Return to NC Webtools</a></p>'; ?>
