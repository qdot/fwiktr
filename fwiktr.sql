DROP TABLE IF EXISTS fwiktr_post_source;
DROP TABLE IF EXISTS fwiktr_post;
DROP TABLE IF EXISTS fwiktr_chain_mechanism;
DROP TABLE IF EXISTS fwiktr_selection_mechanism;
DROP TABLE IF EXISTS fwiktr_picture_source;
DROP TABLE IF EXISTS fwiktr_picture;
DROP TABLE IF EXISTS fwiktr_art;
DROP TABLE IF EXISTS fwiktr_transform_type;
DROP TABLE IF EXISTS fwiktr_transform;

CREATE TABLE fwiktr_post_source
(
	post_source_index INT AUTO_INCREMENT PRIMARY KEY,
	post_source_name VARCHAR(50),
	post_source_url VARCHAR(255)
) ENGINE=InnoDB;

INSERT INTO fwiktr_post_source (post_source_name, post_source_url) VALUES ("Twitter", "http://www.twitter.com");
INSERT INTO fwiktr_post_source (post_source_name, post_source_url) VALUES ("Overheard in New York", "http://www.overheardinnewyork.com");

CREATE TABLE fwiktr_post
(
	post_index INT AUTO_INCREMENT PRIMARY KEY,
	post_source_index INT NOT NULL REFERENCES fwiktr_post_source(post_source_index),
	post_date DATETIME,
	post_text TEXT,
	post_info TEXT
) ENGINE=InnoDB;

CREATE TABLE fwiktr_picture_source
(
	picture_source_index INT AUTO_INCREMENT PRIMARY KEY,
	picture_source_name VARCHAR(50) NOT NULL,
	picture_source_base_url VARCHAR(200) NOT NULL,
	picture_source_site_url_builder VARCHAR(200) NOT NULL,
	picture_source_direct_url_builder VARCHAR(200) NOT NULL
) ENGINE=InnoDB;

INSERT INTO fwiktr_picture_source
(picture_source_name,
picture_source_base_url)
VALUES
("Flickr", "http://www.flickr.com");

INSERT INTO fwiktr_picture_source
(picture_source_name,
picture_source_base_url)
VALUES
("Picasa", "http://www.picasa.com");

CREATE TABLE fwiktr_picture
(
	picture_index INT AUTO_INCREMENT PRIMARY KEY,
	picture_source_index INT NOT NULL REFERENCES fwiktr_picture_source(picture_source_index),
	picture_info TEXT
) ENGINE=InnoDB;

CREATE TABLE fwiktr_transform_type
(
	transform_type_index INT AUTO_INCREMENT PRIMARY KEY,
	transform_type_name VARCHAR(50),
	transform_type_description TEXT
) ENGINE=InnoDB;

INSERT INTO fwiktr_transform_type
(transform_type_name, 
transform_type_description)
VALUES
("Tokenize String",
"Tokenize the string into a list and remote sentinels"
);		  

INSERT INTO fwiktr_transform_type
(transform_type_name,
transform_type_description)
VALUES
("TreeTagger - Nouns Only",
"Run the TreeTagger program against the string, and use all tags returned as NN, NP, NNS, or NPS");

INSERT INTO fwiktr_transform_type
(transform_type_name,
transform_Type_description)
VALUES
("Flickr - Any Tags",
"Search for any tags given (universal OR)");

INSERT INTO fwiktr_transform_type
(transform_type_name,
transform_Type_description)
VALUES
("Flickr - All Tags",
"Search for all tags given (universal AND)");

CREATE TABLE fwiktr_art
(
	art_index INT AUTO_INCREMENT PRIMARY KEY,
	art_tags TEXT,
	art_pos_output TEXT,
	art_date TIMESTAMP DEFAULT NOW(),
	post_index INT REFERENCES fwiktr_post(post_index) ON DELETE CASCADE,
	picture_index INT REFERENCES fwiktr_picture(flickr_index) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE fwiktr_transform
(
	transform_type INT NOT NULL REFERENCES fwiktr_transform_type(transform_type_index),
	art_index INT NOT NULL REFERENCES fwiktr_art(art_index) ON DELETE CASCADE,
	transform_before TEXT,
	transform_after TEXT,
	transform_output TEXT,	
	transform_step INT NOT NULL,
	PRIMARY KEY (art_index, transform_step)
) ENGINE=InnoDB;
