<?php

$art_index = (int)$_GET['art_index'];
if(!is_int($art_index) || $art_index == 0) $art_index = 1;

$link = mysql_connect('mysql.30helensagree.com', 'thirtyhelens_sql', 'carryapen')
    or die('Could not connect: ' . mysql_error());
mysql_select_db('30helensagree') or die('Could not select database');

$get_count = "SELECT MAX(art_index) AS max_count FROM fwiktr_art";
$result = mysql_query($get_count) or die('Count Query failed: ' . mysql_error());
$row = mysql_fetch_object($result);
$full_count = $row->max_count;

if($art_index > $full_count) $art_index = $full_count - 1;

$get_art = "SELECT 
* FROM fwiktr_art
LEFT JOIN fwiktr_posts USING (post_index)
LEFT JOIN fwiktr_twitter_info USING (post_index)
LEFT JOIN fwiktr_post_sources ON(fwiktr_posts.source_index = fwiktr_post_sources.source_index)
LEFT JOIN fwiktr_flickr ON (fwiktr_art.flickr_index = fwiktr_flickr.flickr_index)
WHERE art_index = ".$art_index;

$result = mysql_query($get_art) or die('Art Query failed: ' . mysql_error());

if(mysql_num_rows($result) == 0) die('Index does not exist');

$row = mysql_fetch_object($result);
$flickr_photo_url = "http://farm".$row->flickr_farm.".static.flickr.com/".$row->flickr_server."/".$row->flickr_photo_id."_".$row->flickr_secret.".jpg";
$flickr_web_url = "http://www.flickr.com/photos/".$row->flickr_owner_id."/".$row->flickr_photo_id;

$art_refresh = (int)$_GET['art_refresh'];
if(!is_int($art_refresh) || $art_refresh == 0) $art_refresh = 0;
else if($art_refresh < 5) $art_refresh = 5;

print "
<HTML>
<HEAD>
";

if($art_refresh >= 1)
{
	print "<meta http-equiv='refresh' content='".$art_refresh.";url=http://30helensagree.com/fwiktr/fwiktr_view.php?art_refresh=".$art_refresh."&art_index=".($art_index+1)."'>";
}

print "
<TITLE>fwiktr generation for post ".$row->post_index."</TITLE>
</HEAD>
<BODY>
<A HREF='fwiktr_view.php?art_index=".(string)($art_index-1)."'>Previous</A><BR>
<A HREF='fwiktr_view.php?art_index=".(string)($art_index+1)."'>Next</A><BR>
<BR><BR>
<FONT SIZE=+2>".$row->post_text."</FONT><BR>\n
<A HREF='".$flickr_web_url."'><IMG SRC='".$flickr_photo_url."' BORDER=0></A><BR>
<B>POST TAGS:</B>
".$row->art_tags."<BR>\n
<B>POS POS OUTPUT:</B><BR>
<PRE>
".htmlentities($row->art_pos_output)."
</PRE><BR>\n
<BR><BR>
<FORM METHOD=GET>
Seconds until refresh (cycles pictures sequentially, minimum 5 seconds, set to 0 to stop): <INPUT TYPE='TEXT' NAME='art_refresh' VALUE=".$art_refresh."><BR>
Goto Art (Total Artses: ".$full_count.") : <INPUT TYPE='TEXT' NAME='art_index' VALUE=".$art_index."><BR>
<INPUT TYPE=SUBMIT VALUE=Artify>
</FORM>
</BODY>
</HTML>
";
?>