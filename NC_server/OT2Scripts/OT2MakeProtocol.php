<h2>Upload files to produce a custom OT2 protocol</h2>
<p>Locate all necessary files and submit</p>
<p><i>(version 1.0 SP 2021_09_17)</i></p>

<img src="http://10.112.84.39/pictures/OT-2.png" />

<form method="post" action='OT2MakeProtocol_upload.php' enctype='multipart/form-data'>
  <input type="reset" style="font-size:14px";>
  <hr>
  <h4>Template protocol file (.py):</h4>
  <input name="upload[]" type="file" />
  <h4>Configuration file (.yaml):</h4>
  <input name="upload[]" type="file" />
  <h4>CSV file (when relevant, .csv):</h4>
  <input name="upload[]" type="file" />
  <br><br>
  <hr>
  <input type="submit" name="submit" value="Submit" style="font-size:14px";>
</form>

</body>
</html>
