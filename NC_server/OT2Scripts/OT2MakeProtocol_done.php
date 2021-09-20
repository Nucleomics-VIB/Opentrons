<html>
 <head>
  <title>OT2 script results</title>
 </head>
 <body>

 <?php echo '<p><a href=http://10.112.84.39/cgi-bin/OT2Scripts/OT2DownloadScript.php>Download your script</a></p>'; ?>
 <?php echo '<p><a href=http://10.112.84.39/webtools/Workflow.htm>Return to NC Webtools</a></p>'; ?>
 <hr>
 <?php chdir('/var/www/cgi-bin/OT2uploads/'); ?>
 <h3><?php echo "The resulting protocol is as follows:" ?></h3>
 <hr>
 <pre><?php echo nl2br( file_get_contents( "NC_protocol.py" ) ) ?></pre>
 <hr>

 </body>
</html>
