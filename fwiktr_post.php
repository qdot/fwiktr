<?php

$text = urldecode($_POST['fwiktr_post']);

$doc = new SimpleXMLElement($text);
$info = $doc;

$link = mysql_connect('mysql.30helensagree.com', 'thirtyhelens_sql', 'carryapen')
    or die('Could not connect: ' . mysql_error());
mysql_select_db('30helensagree') or die('Could not select database');

$post_info = $doc->xpath("/post_info");

//Query Order:
// - Post OR
// - Picture THEN
// - Art THEN
// - Transforms

$post_sql[0] =
"INSERT INTO fwiktr_post (
post_source_index,
post_date,
post_text,
post_info)
VALUES
(
".(string)$info->post[0]->post_source.",
'".(string)$info->post[0]->post_date."',
'".mysql_real_escape_string((string)$info->post[0]->post_text)."',
'".mysql_real_escape_string((string)($info->post_info[0]->asXml()))."'
)";

$post_sql[1] =
"INSERT INTO fwiktr_picture (
picture_source_index,
picture_info)
VALUES
(
".(string)$info->picture[0]->picture_source.",
'".mysql_real_escape_string((string)($info->picture_info[0]->asXml()))."'
)";

$post_sql[2] = "INSERT INTO fwiktr_art (
art_tags, 
post_index, 
picture_index
) (SELECT 
'".(string)$info->art[0]->art_tags."',
MAX(p.post_index),
MAX(f.picture_index)
FROM
fwiktr_post AS p,
fwiktr_picture AS f)";

foreach ($info->transforms->transform as $transform)
	{
		$transform_query = "
INSERT INTO fwiktr_transform (
art_index,
transform_step,
transform_type_index,
transform_before,
transform_after,
transform_output
)
(SELECT
MAX(a.art_index),
".$transform->transform_step.",
".$transform->transform_index.",
'".mysql_real_escape_string((string)$transform->transform_before)."',
'".mysql_real_escape_string((string)$transform->transform_after)."',
'".mysql_real_escape_string((string)$transform->transform_output)."' FROM
fwiktr_art AS a)";
		array_push($post_sql, $transform_query);
	}

// Performing SQL query
$result = mysql_query("BEGIN;") or die('Query failed: ' . mysql_error());
$has_error = false;
foreach ($post_sql as $query)
{
	$result = mysql_query($query);
	if(!$result)
	{
		print("QUERY FAILURE: ".$query."\n");
		print("Query Failed: ".mysql_error()."\n");
		$has_error = true;
		$result = mysql_query("ROLLBACK;");
		break;
	}
}
if(!$has_error) $result = mysql_query("COMMIT;") or print('Query failed: ' . mysql_error());

?>