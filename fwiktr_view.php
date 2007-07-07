<?php

function RunTemplateSubstitution($xml_node)
{
	print("Running template substitution for ".$xml_node->getName());
	foreach($xml_node->children() as $node)
	{
		if(count($node->children()) != 0) RunTemplateSubstituion($node);
	}	
}

function FormatTagNodes($xml_node)
{
	$tag_str = "";
	foreach($xml_node->children() as $key => $tag)
	{
		$tag_str .= "{$tag},";
	}
	return substr($tag_str, 0, strlen($tag_str)-1);
}

$art_index = (int)$_GET['art_index'];
if(!is_int($art_index) || $art_index == 0) $art_index = 1;

$link = mysql_connect('mysql.30helensagree.com', 'thirtyhelens_sql', 'carryapen')
    or die('Could not connect: ' . mysql_error());
mysql_select_db('30helensagree') or die('Could not select database');

$get_count = "SELECT COUNT(*) AS max_count FROM fwiktr_xml";
$result = mysql_query($get_count) or die('Count Query failed: ' . mysql_error());
$row = mysql_fetch_object($result);
$full_count = $row->max_count;

if($art_index > $full_count) $art_index = $full_count - 1;

$get_art = "SELECT * FROM fwiktr_xml LIMIT ".$art_index.", 1";

$result = mysql_query($get_art) or die('Art Query failed: ' . mysql_error());

if(mysql_num_rows($result) == 0) die('Index does not exist');

$row = mysql_fetch_object($result);

$doc = new SimpleXMLElement(stripslashes($row->xml_text));

//Art Node
/* 
$art_node = $doc->art

//Language Node
$language_node = $doc->language

//Picture Node
$picture_node = $doc->picture

//Post Node
$post_node = $doc->post

//Transform Node
$transforms_node = $doc->transforms
*/
//Full Page

$flickr = $doc->picture->flickr;
 
$flickr_photo_url = "http://farm".$flickr->flickr_farm.".static.flickr.com/".$flickr->flickr_server."/".$flickr->flickr_photo_id."_".$flickr->flickr_secret.".jpg";
$flickr_web_url = "http://www.flickr.com/photos/".$flickr->flickr_owner_id."/".$flickr->flickr_photo_id;

$art_refresh = (int)$_GET['art_refresh'];
if(!is_int($art_refresh) || $art_refresh == 0) $art_refresh = 0;
else if($art_refresh < 5) $art_refresh = 5;

print "
<HTML>
<HEAD>
";

if($art_refresh >= 1)
{
	print "<meta http-equiv='refresh' content='{$art_refresh};url=http://30helensagree.com/fwiktr/fwiktr_view.php?art_refresh={$art_refresh}&art_index=".($art_index+1)."'>";
}

print ("
<TITLE>fwiktr generation for post {$doc->post->post_text}</TITLE>
</HEAD>
<BODY>
<A HREF='fwiktr_view.php?art_index=".(string)($art_index-1)."'>Previous</A><BR>
<A HREF='fwiktr_view.php?art_index=".(string)($art_index+1)."'>Next</A><BR>
<BR><BR>
<FONT SIZE=+2>{$doc->post->post_text}</FONT><BR>\n
<A HREF='{$flickr_web_url}'><IMG SRC='{$flickr_photo_url}' BORDER=0></A><BR>
<B>POST TAGS:</B>
");
print(FormatTagNodes($doc->art->tags)."<BR>");
print("<BR>I started with<BR>'{$doc->post->post_text}'<BR>For language, I used<BR>{$doc->language->language_method}<BR>which<BR>{$doc->language->language_description}<BR>to give me back<BR>{$doc->language->language_result}<BR>as the post langauge.<BR>To make the art, I ran<BR>");
$i = 0;
foreach($doc->transforms->children() as $transform)
{
	if($i) print("And then I ran<BR>");
	print("{$transform->transform_name}<BR>which<BR>{$transform->transform_description}<BR>");
	if($transform->transform_output != "")
	{
		print("And that gave me back<BR><PRE>{$transform->transform_output}</PRE><BR>");
	}
	if(count($transform->transform_after->tags->children()) != 0)
	{
		print("I ended up with<BR>");
		print(FormatTagNodes($transform->transform_after->tags));			
		print("<BR>");
	}
	$i = 1;
}
print("
<BR>\n
<BR><BR>
<FORM METHOD=GET>
Seconds until refresh (cycles pictures sequentially, minimum 5 seconds, set to 0 to stop): <INPUT TYPE='TEXT' NAME='art_refresh' VALUE=".$art_refresh."><BR>
Goto Art (Total Artses: ".$full_count.") : <INPUT TYPE='TEXT' NAME='art_index' VALUE=".$art_index."><BR>
<INPUT TYPE=SUBMIT VALUE=Artify>
</FORM>
</BODY>
</HTML>
");
?>