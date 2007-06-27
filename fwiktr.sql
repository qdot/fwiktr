DROP TABLE IF EXISTS fwiktr_post_sources;
DROP TABLE IF EXISTS fwiktr_posts;
DROP TABLE IF EXISTS fwiktr_twitter_info;
DROP TABLE IF EXISTS fwiktr_flickr;
DROP TABLE IF EXISTS fwiktr_chain_mechanism;
DROP TABLE IF EXISTS fwiktr_selection_mechanism;
DROP TABLE IF EXISTS fwiktr_art;

CREATE TABLE fwiktr_post_sources
(
	source_index INT AUTO_INCREMENT PRIMARY KEY,
	source_name VARCHAR(255),
	source_base_url VARCHAR(255)
) ENGINE=InnoDB;

INSERT INTO fwiktr_post_sources (source_name, source_base_url) VALUES ("Twitter", "http://www.twitter.com");
INSERT INTO fwiktr_post_sources (source_name, source_base_url) VALUES ("Overheard in New York", "http://www.overheardinnewyork.com");

CREATE TABLE fwiktr_posts
(
	post_index INT AUTO_INCREMENT PRIMARY KEY,
	source_index INT NOT NULL REFERENCES fwiktr_post_sources(source_index),
	post_text TEXT,
	post_date DATE
) ENGINE=InnoDB;

CREATE TABLE fwiktr_twitter_info
(
	post_index INT PRIMARY KEY REFERENCES fwiktr_posts(post_index),
	twitter_post_id INT NOT NULL UNIQUE,
	twitter_author_id INT NOT NULL UNIQUE,
	twitter_author_name VARCHAR(30) NOT NULL,
	twitter_location VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE fwiktr_flickr
(
	flickr_index INT AUTO_INCREMENT PRIMARY KEY,
	flickr_server INT,
	flickr_farm INT,
	flickr_photo_id VARCHAR(50),
	flickr_owner_id VARCHAR(50),
	flickr_secret VARCHAR(50),
	flickr_title VARCHAR(200)
) ENGINE=InnoDB;

CREATE TABLE fwiktr_chain_mechanism
(
	chain_mechanism_index INT AUTO_INCREMENT PRIMARY KEY,
	chain_mechanism_name VARCHAR(50)
) ENGINE=InnoDB;

INSERT INTO fwiktr_chain_mechanism (chain_mechanism_name) VALUES ('Any');
INSERT INTO fwiktr_chain_mechanism (chain_mechanism_name) VALUES ('All');

CREATE TABLE fwiktr_selection_mechanism
(
	selection_mechanism_index INT AUTO_INCREMENT PRIMARY KEY,
	selection_mechanism_name VARCHAR(50)
) ENGINE=InnoDB;

INSERT INTO fwiktr_selection_mechanism (selection_mechanism_name) VALUES ('Random');

CREATE TABLE fwiktr_art
(
	art_index INT AUTO_INCREMENT PRIMARY KEY,
	art_tags TEXT,
	art_pos_output TEXT,
	art_date TIMESTAMP DEFAULT NOW(),
	art_total_returned INT,
	chain_mechanism_index INT DEFAULT 1 REFERENCES fwiktr_chain_mechanism(chain_mechanism_index),
	selection_mechanism_index INT DEFAULT 1 REFERENCES fwiktr_selection_mechanism(selection_mechanism_index),
	post_index INT REFERENCES fwiktr_posts(post_index),
	flickr_index INT REFERENCES fwiktr_flickr(flickr_index),
	UNIQUE KEY(post_index, flickr_index)
) ENGINE=InnoDB;
