<?php
chdir('/var/www/cgi-bin/OT2MakeProtocol/uploads/');

// cleanup for next run
$files = glob("/var/www/cgi-bin/OT2MakeProtocol/uploads/*"); // get all file names
foreach($files as $file){ // iterate files
  if(is_file($file)) {
    unlink($file); // delete file
  }
};
?>
