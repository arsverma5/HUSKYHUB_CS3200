

DROP DATABASE IF EXISTS HuskyHub;
CREATE DATABASE IF NOT EXISTS HuskyHub;


USE HuskyHub;


DROP TABLE IF EXISTS student;
CREATE TABLE student(
   stuId int PRIMARY KEY AUTO_INCREMENT,
   firstName varchar(50) NOT NULL,
   lastName varchar(50) NOT NULL,
   email varchar(50) NOT NULL UNIQUE,
   phone varchar(15) NOT NULL,
   bio tinytext,
   campus char(5),
   major varchar(50),
   joinDate datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   accountStatus ENUM('active','suspended','deleted') NOT NULL DEFAULT 'active',
   verifiedStatus tinyint(1) DEFAULT FALSE,
   profilePhotoUrl varchar(500),
   INDEX idx_first_name (firstName),
   INDEX idx_last_name (lastName)
);


DROP TABLE IF EXISTS category;
CREATE TABLE category(
   categoryId int PRIMARY KEY AUTO_INCREMENT,
   name varchar(50) NOT NULL,
   type ENUM('service','product') NOT NULL,
   description text
);


DROP TABLE IF EXISTS listing;
CREATE TABLE listing(
   listingId int PRIMARY KEY AUTO_INCREMENT,
   categoryId int,
   providerId int DEFAULT 0,
   title varchar(100) NOT NULL,
   description mediumtext NOT NULL,
   price decimal(7, 2) NOT NULL,
   unit varchar(15),
   imageUrl varchar(150),
   createDate datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   lastUpdate datetime NOT NULL,
   listingStatus ENUM('draft','active','inactive','removed') NOT NULL,
   FOREIGN KEY (categoryId) REFERENCES category(categoryId)
                   ON UPDATE CASCADE
                   ON DELETE RESTRICT,
   FOREIGN KEY (providerId) REFERENCES student(stuId)
                   ON UPDATE CASCADE
                   ON DELETE SET NULL,
   INDEX idx_listing_category (categoryId),
   INDEX idx_listing_provider (providerId)
);


DROP TABLE IF EXISTS transact;
CREATE TABLE transact(
   transactId int PRIMARY KEY AUTO_INCREMENT,
   buyerId int NOT NULL,
   listId int NOT NULL,
   bookDate datetime NOT NULL,
   transactStatus ENUM('requested', 'confirmed', 'completed', 'cancelled') NOT NULL,
   fulfillmentDate datetime,
   paymentAmt decimal(7, 2),
   platformFee decimal(7, 2),
   agreementDetails mediumtext,
   FOREIGN KEY (listId) REFERENCES listing(listingId)
                       ON UPDATE CASCADE
                       ON DELETE RESTRICT,
   FOREIGN KEY (buyerId) REFERENCES student(stuId)
                       ON UPDATE CASCADE
                       ON DELETE RESTRICT,
   INDEX idx_transact_buyer (buyerId),
   INDEX idx_transact_listing (listId)
);


DROP TABLE IF EXISTS availability;
CREATE TABLE availability(
   listId int NOT NULL,
   availabilityId int NOT NULL PRIMARY KEY AUTO_INCREMENT,
   startTime datetime NOT NULL,
   endTime datetime NOT NULL,
   UNIQUE (listId, startTime, endTime),
   FOREIGN KEY (listId) REFERENCES listing(listingId)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
   INDEX idx_availability_listing (listId)
);


DROP TABLE IF EXISTS review;
CREATE TABLE review(
   reviewId int PRIMARY KEY AUTO_INCREMENT,
   listId int NOT NULL,
   reviewerId int DEFAULT 0,
   rating int NOT NULL CHECK (rating BETWEEN 1 AND 5),
   createDate datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   reviewText text,
   FOREIGN KEY (listId) REFERENCES listing(listingId)
                  ON UPDATE CASCADE
                  ON DELETE RESTRICT,
   FOREIGN KEY (reviewerId) REFERENCES student(stuId)
                  ON UPDATE CASCADE
                  ON DELETE SET NULL,
   INDEX idx_review_reviewer (reviewerId),
   INDEX idx_review_listing (listId)
);


DROP TABLE IF EXISTS admin;
CREATE TABLE admin(
   adminId int PRIMARY KEY AUTO_INCREMENT,
   firstName varchar(50) NOT NULL,
   lastName varchar(50) NOT NULL,
   email varchar(50) NOT NULL UNIQUE,
   accountStatus ENUM('active', 'deleted') NOT NULL DEFAULT 'active'
);


DROP TABLE IF EXISTS report;
CREATE TABLE report(
   reportId int PRIMARY KEY AUTO_INCREMENT,
   reportingStuId int NOT NULL,
   reportedStuId int NOT NULL,
   reportedListingId int,
   adminId int,
   reportDate datetime NOT NULL,
   resolutionDate datetime,
   reason text NOT NULL,
   reportDetails mediumtext,
   FOREIGN KEY (reportingStuId) REFERENCES student(stuId)
                  ON UPDATE CASCADE
                  ON DELETE RESTRICT,
   FOREIGN KEY (reportedStuId) REFERENCES student(stuId)
                  ON UPDATE CASCADE
                  ON DELETE RESTRICT,
   FOREIGN KEY (reportedListingId) REFERENCES listing(listingId)
                  ON UPDATE CASCADE
                  ON DELETE RESTRICT,
   FOREIGN KEY (adminId) REFERENCES admin(adminId)
                  ON UPDATE CASCADE
                  ON DELETE RESTRICT
);


DROP TABLE IF EXISTS suspension;
CREATE TABLE suspension(
   suspensionId int PRIMARY KEY AUTO_INCREMENT,
   stuId int NOT NULL,
   reportId int,
   type ENUM('temp', 'perm') NOT NULL,
   startDate datetime NOT NULL,
   endDate datetime,
   FOREIGN KEY (stuId) REFERENCES student(stuId)
                      ON UPDATE CASCADE
                      ON DELETE RESTRICT,
   FOREIGN KEY (reportId) REFERENCES report(reportId)
                      ON UPDATE CASCADE
                      ON DELETE RESTRICT
);


DROP TABLE IF EXISTS admin_notes;
CREATE TABLE admin_notes(
   noteId int PRIMARY KEY AUTO_INCREMENT,
   adminId int NOT NULL,
   reportId int NOT NULL,
   createDate datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   content mediumtext,
   FOREIGN KEY (adminId) REFERENCES admin(adminId)
                       ON UPDATE CASCADE
                       ON DELETE RESTRICT,
   FOREIGN KEY (reportId) REFERENCES report(reportId)
                       ON UPDATE CASCADE
                       ON DELETE RESTRICT
);
