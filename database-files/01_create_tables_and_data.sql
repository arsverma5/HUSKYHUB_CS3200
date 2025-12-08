

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
   profilePhotoUrl varchar(150),
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


-- --------------------------------------------
-- SAMPLE DATA
-- --------------------------------------------


-- Insert sample students
INSERT INTO student (stuId, firstName, lastName, email, phone, major, verifiedStatus, bio, joinDate) VALUES
(1, 'Emma', 'Chen', 'chen.em@northeastern.edu', '617-555-0101', 'Computer Science', TRUE, 'CS major looking for tutoring help', '2025-08-15 10:30:00'),
(2, 'Michael', 'Rodriguez', 'rodriguez.m@northeastern.edu', '617-555-0102', 'Computer Science', TRUE, 'CS tutor specializing in Python and data structures', '2025-09-02 14:20:00'),
(3, 'Jessica', 'Martinez', 'martinez.j@northeastern.edu', '617-555-0103', 'Business Administration', TRUE, 'Experienced tutor for Calc and Spanish', '2025-09-10 09:15:00'),
(4, 'John', 'Doe', 'doe.j@northeastern.edu', '617-555-0104', 'Marketing', TRUE, 'Student looking for services', '2025-10-05 16:45:00'),
(5, 'Sarah', 'Kim', 'kim.s@northeastern.edu', '617-555-0105', 'Engineering', FALSE, 'New student', '2025-11-20 11:00:00'),
(6, 'Priya', 'Singh', 'priya.singh@northeastern.edu', '617-555-0106', 'Data Science', TRUE, 'Interested in ML projects', '2025-12-03 09:10:00'),
(7, 'Alex', 'Nguyen', 'alex.nguyen@northeastern.edu', '617-555-0107', 'Design', FALSE, 'New to HuskyHub, exploring services', '2025-12-06 18:25:00');


-- Insert sample categories
INSERT INTO category (categoryId, name, type, description) VALUES
(1, 'Tutoring', 'service', 'Academic tutoring services'),
(2, 'Moving Help', 'service', 'Help with moving and furniture'),
(3, 'Marketplace', 'product', 'Buy and sell items'),
(4, 'Tech Help', 'service', 'Computer and tech support');


-- Insert sample listings
INSERT INTO listing (listingId, categoryId, providerId, title, description, price, unit, createDate, lastUpdate, listingStatus) VALUES
(1, 1, 2, 'Python Tutoring', 'Expert Python tutoring for CS courses', 30.00, 'per hour', '2025-09-05 08:00:00', '2025-11-30 10:15:00', 'active'),
(2, 1, 3, 'Calculus Tutoring', 'Help with Calculus I and II', 25.00, 'per hour', '2025-09-12 13:30:00', '2025-11-28 15:45:00', 'active'),
(3, 2, 2, 'Moving Help', 'Help with apartment moves', 50.00, 'flat rate', '2025-10-01 09:45:00', '2025-12-02 12:00:00', 'active'),
(4, 4, 2, 'Laptop Troubleshooting', 'Fixes, cleanup, and tune-ups for student laptops', 40.00, 'per hour', '2025-12-02 14:00:00', '2025-12-05 11:20:00', 'active'),
(5, 1, 3, 'Statistics Crash Session', 'Intensive 2-hour stats prep for finals', 60.00, 'flat rate', '2025-12-04 17:30:00', '2025-12-06 10:05:00', 'active');


-- Insert sample availability
INSERT INTO availability (listId, startTime, endTime) VALUES
(1, '2025-11-25 14:00:00', '2025-11-25 15:00:00'),
(1, '2025-11-25 16:00:00', '2025-11-25 17:00:00'),
(2, '2025-11-26 10:00:00', '2025-11-26 11:00:00');


-- Insert sample reviews
INSERT INTO review (listId, reviewerId, rating, reviewText) VALUES
(1, 4, 5, 'Great tutor! Very helpful and patient.'),
(1, 5, 4, 'Good session, learned a lot.'),
(2, 1, 5, 'Excellent Calculus tutor!');


-- Insert sample admins
INSERT INTO admin (adminId, firstName, lastName, email) VALUES
(1, 'Timothy', 'Green', 'green.t@northeastern.edu'),
(2, 'Admin', 'User', 'admin@northeastern.edu');


-- Insert sample reports (optional - for testing admin queries)
INSERT INTO report (reportId, reportingStuId, reportedStuId, reportedListingId, adminId, reportDate, resolutionDate, reason, reportDetails) 
VALUES
(1, 1, 4, NULL, NULL, NOW(), NULL, 'Inappropriate listing content', 'User posted suspicious pricing and contact information');


-- Insert sample transactions
INSERT INTO transact (transactId, buyerId, listId, bookDate, transactStatus, fulfillmentDate, paymentAmt, platformFee, agreementDetails) VALUES
(1, 1, 1, '2025-12-01 15:31:03', 'completed', '2025-12-01 16:31:03', 30.00, 3.00, '1 hour Python tutoring'),
(2, 4, 1, '2025-11-25 16:00:00', 'completed', '2025-11-25 17:00:00', 30.00, 3.00, 'Python session for project help'),
(3, 5, 2, '2025-11-15 10:00:00', 'completed', '2025-11-15 11:00:00', 25.00, 2.50, 'Calculus tutoring - 1 hour'),
(4, 3, 3, '2025-10-20 09:00:00', 'completed', '2025-10-20 12:00:00', 50.00, 5.00, 'Moving help - 3 hours'),
(5, 2, 3, '2025-10-25 11:00:00', 'cancelled', NULL, 0.00, 0.00, 'Cancelled booking'),
(6, 1, 2, '2025-09-20 12:00:00', 'completed', '2025-09-20 13:00:00', 25.00, 2.50, 'Old transaction sample'),
(7, 4, 1, '2025-11-05 14:00:00', 'completed', '2025-11-05 15:00:00', 30.00, 3.00, 'Booked, awaiting fulfillment'),
(8, 2, 1, '2025-12-03 09:30:00', 'completed', '2025-12-03 10:30:00', 30.00, 3.00, 'Morning Python consult'),
(9, 5, 2, '2025-12-05 18:00:00', 'completed', '2025-12-05 19:00:00', 25.00, 2.50, 'Calc test prep'),
(10, 3, 3, '2025-12-06 13:15:00', 'completed', '2025-12-06 14:45:00', 50.00, 5.00, 'Apartment move assistance'),
(11, 1, 2, '2025-12-07 20:00:00', 'cancelled', NULL, 0.00, 0.00, 'Same-day cancellation');


