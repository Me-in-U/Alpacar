CREATE TABLE `User` (
    `user_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `username` varchar(255) NOT NULL,
    `nickname` varchar(255) UNIQUE NOT NULL,
    `password` varchar(255) NOT NULL,
    `phone` varchar(255) NOT NULL,
    `email` varchar(255) NOT NULL,
    `score` int NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT(now()),
    `updated_at` TIMESTAMP NOT NULL DEFAULT(now())
);

CREATE TABLE `Vehicle` (
    `vehicle_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `license_plate` varchar(255) UNIQUE NOT NULL,
    `user_id` int UNIQUE NOT NULL,
    `model_id` int NOT NULL
);

CREATE TABLE `VehicleModel` (
    `model_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `brand` varchar(255) NOT NULL,
    `model_name` varchar(255) NOT NULL,
    `size_class` enum(compact, midsize, suv) NOT NULL,
    `image_url` varchar(255) NOT NULL
);

CREATE TABLE `ParkingSpace` (
    `space_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `zone` varchar(255) NOT NULL,
    `slot_number` int NOT NULL,
    `size_class` enum(compact, midsize, suv) NOT NULL,
    `status` enum(free, occupied, reserved) NOT NULL
);

CREATE TABLE `ParkingAssignment` (
    `assignment_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `user_id` int NOT NULL,
    `vehicle_id` int NOT NULL,
    `space_id` int NOT NULL,
    `start_time` datetime NOT NULL,
    `end_time` datetime,
    `status` varchar(255) NOT NULL
);

CREATE TABLE `VehicleEvent` (
    `event_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `vehicle_id` int NOT NULL,
    `event_type` varchar(255) NOT NULL,
    `timestamp` datetime NOT NULL
);

CREATE TABLE `UserScoreHistory` (
    `history_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `user_id` int NOT NULL,
    `assignment_id` int NOT NULL,
    `score` int NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT(now())
);

CREATE TABLE `CarNumberPlateModelMapping` (
    `mapping_id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,
    `license_plate` varchar(255) UNIQUE NOT NULL,
    `model_id` int NOT NULL
);

ALTER TABLE `Vehicle`
ADD FOREIGN KEY (`user_id`) REFERENCES `User` (`user_id`);

ALTER TABLE `Vehicle`
ADD FOREIGN KEY (`model_id`) REFERENCES `VehicleModel` (`model_id`);

ALTER TABLE `ParkingAssignment`
ADD FOREIGN KEY (`user_id`) REFERENCES `User` (`user_id`);

ALTER TABLE `ParkingAssignment`
ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicle` (`vehicle_id`);

ALTER TABLE `ParkingAssignment`
ADD FOREIGN KEY (`space_id`) REFERENCES `ParkingSpace` (`space_id`);

ALTER TABLE `VehicleEvent`
ADD FOREIGN KEY (`vehicle_id`) REFERENCES `Vehicle` (`vehicle_id`);

ALTER TABLE `UserScoreHistory`
ADD FOREIGN KEY (`user_id`) REFERENCES `User` (`user_id`);

ALTER TABLE `UserScoreHistory`
ADD FOREIGN KEY (`assignment_id`) REFERENCES `ParkingAssignment` (`assignment_id`);

ALTER TABLE `CarNumberPlateModelMapping`
ADD FOREIGN KEY (`model_id`) REFERENCES `VehicleModel` (`model_id`);