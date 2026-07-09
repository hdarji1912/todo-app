-- MySQL Database Schema for Todo Application
-- This script is auto-loaded when the MySQL container initialises
-- Create database (already exists, but just in case)
CREATE DATABASE IF NOT EXISTS mydb;
-- Use the database
USE mydb;

-- ─────────────────────────────────────────────
-- USERS TABLE
-- Stores registered user accounts
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- AUTH LOGS TABLE
-- Tracks every login / logout / failed attempt
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,                          -- NULL for failed attempts (unknown user)
    action ENUM('login', 'logout', 'failed') NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,       -- supports IPv4 and IPv6
    username_attempted VARCHAR(50) DEFAULT NULL, -- captures username even on failed login
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- TODOS TABLE  (original — untouched)
-- Only addition: user_id foreign key column
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS todos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task VARCHAR(255) NOT NULL,
    status ENUM('pending', 'completed') DEFAULT 'pending',
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    user_id INT NULL,                          -- links each task to its owner
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_deleted (deleted),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- SAMPLE DATA  (original — untouched)
-- ─────────────────────────────────────────────
-- Insert sample data (only if the table is empty)
INSERT INTO todos (task, status)
SELECT * FROM (SELECT 'Learn Docker basics' as task, 'completed' as status) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM todos LIMIT 1);
INSERT INTO todos (task, status) VALUES
    ('Build Flask application', 'completed'),
    ('Create docker-compose.yml', 'completed'),
    ('Set up Jenkins pipeline', 'pending'),
    ('Deploy to production', 'pending')
ON DUPLICATE KEY UPDATE task=task;  -- Avoid duplicates