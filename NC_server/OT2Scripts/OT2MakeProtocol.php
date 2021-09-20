<html>
<body>
<h2>This script replaces the online protocol GUI where users can change variables and adapt parameters to produce a final protocol.</h2>
<p><i>(version 1.0 SP 2021_09_20)</i></p>

<img src="http://10.112.84.39/pictures/OT-2.png" width="300px" />

<h3>OT2MakeProtocol Info:</h3>

<p>This webtool requires uploading several user-edited files in order to do its job.</p>

<ul>
<li>The <b>template</b> file contains the OT2 protocol script with placeholders for user editable variables (<i>see example file</i>)</li>
<li>The <b>yaml</b> (plain text) file contains the names of the placeholders and the user-defined values to replace them in the code (<i>see example file</i>)</li>
<li>Finally, a <b>CSV</b> file can optionally be uploaded when a protocol requires a list of actions / plate locations
(eg cherry picking across wells of plates; <i>see example file</i>).</li>
</ul>

<b>Note:</b> when present, the CSV file should be saved with comma-separators (',' and not ';') and saved as a plain text file from your favorite editor.

<?php include 'OT2Cleanup.php'; ?>

<form method="post" action='OT2MakeProtocol_upload.php' enctype='multipart/form-data'>
  <h3>Select the proper files for this job</h3>
  <input type="reset" style="font-size:14px";>
  <hr>
  <h4>Template protocol file (.py):
  <input name="upload[]" type="file" /></h4>
  <h4>Configuration file (.yaml):
  <input name="upload[]" type="file" /></h4>
  <h4>CSV file (when relevant, .csv):
  <input name="upload[]" type="file" /></h4>
  <p>the user is responsible for the correctness of the files, no control is done in the code!</p>
  <br>
  <input type="submit" name="submit" value="Submit" style="font-size:14px";>
</form>

<hr>
<h4>You can <?php echo '<a href=http://10.112.84.39/cgi-bin/OT2MakeProtocol/OT2DownloadTestData.php>Download here</a>'; ?> a zip with example files</h4>
</body>
</html>
