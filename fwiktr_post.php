<?php

$doc = new SimpleXMLElement($_POST['fwiktr_post']);
$info = $doc->post[0];

$post_sql = "INSERT INTO fwiktr_posts (
source_index,
post_url,
post_text,
post_date)
VALUES
(
".(string)$info['post_source'].",
'".(string)$info->url."',
'".(string)$info->text."',
'".(string)$info['post_date']."'
);";

if($info['post_source'] == 1)
  {
    $twitter_sql = "
INSERT INTO fwiktr_twitter_info (
post_index,
twitter_author_name,
twitter_location,
twitter_post_id,
twitter_author_id)
(SELECT MAX(t.post_index),
'".(string)$info->twitter->twitter_author_name."',
'".(string)$info->twitter->twitter_location."',
".(string)$info->twitter->twitter_post_id.",
".(string)$info->twitter->twitter_author_id."
FROM fwiktr_posts AS t);
";
  }

$flickr_sql = "INSERT INTO fwiktr_flickr (
flickr_server,
flickr_farm,
flickr_photo_id,
flickr_owner_id,
flickr_secret,
flickr_title)
VALUES
(
".(string)$info['flickr_server'].",
".(string)$info['flickr_farm'].",
'".(string)$info['flickr_photoid']."',
'".(string)$info['flickr_ownerid']."',
'".(string)$info['flickr_secret']."',
'".(string)$info['flickr_title']."'
);";

$art_sql = "INSERT INTO fwiktr_art (
art_tags, 
art_pos_output, 
art_total_returned, 
post_index, 
flickr_index
) (SELECT 
'".(string)$doc->post[0]->tags."',
'".(string)$doc->post[0]->pos_output."',
".(string)$doc->post[0]['flickr_total'].",
MAX(p.post_index),
MAX(f.flickr_index)
FROM fwiktr_posts AS p,
fwiktr_flickr AS f);";

print $post_sql."\n";
print $twitter_sql."\n";
print $flickr_sql."\n";
print $art_sql."\n";
?>