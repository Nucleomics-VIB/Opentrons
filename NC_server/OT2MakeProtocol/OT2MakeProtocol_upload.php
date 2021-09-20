<?php
for($i=0; $i<3; $i++) {
 $tmpFilePath = $_FILES['upload']['tmp_name'][$i];
  if ($tmpFilePath != ""){
  $file[$i] = $newFilePath = "/var/www/cgi-bin/OT2MakeProtocol/uploads/" . $_FILES['upload']['name'][$i];
    if(move_uploaded_file($tmpFilePath, $newFilePath)) {
    }
  }
}

// run it
$cmd = "/var/www/cgi-bin/OT2MakeProtocol/OT_inject_params.sh -i " . basename($file[0]) . " -y " . basename($file[1]) . " -o NC_protocol.py ;";
echo "<pre># command: " . $cmd . "</pre>";

chdir('/var/www/cgi-bin/OT2MakeProtocol/uploads');
$cmdresult = shell_exec("$cmd");

// echo script results
echo "<pre>" . $cmdresult . "</pre>";

header("Location: http://10.112.84.39/cgi-bin/OT2MakeProtocol/OT2MakeProtocol_done.php");
?>
