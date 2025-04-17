-- Create Database
CREATE DATABASE placement_portal;
USE placement_portal;

-- Create Tables
CREATE TABLE Department (
    department_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    hod VARCHAR(100)
);

CREATE TABLE Student (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    department_id INT,
    cgpa DECIMAL(3,2),
    graduation_year INT,
    contact_number VARCHAR(15),
    resume_path VARCHAR(255),
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);

CREATE TABLE Company (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    description TEXT,
    industry VARCHAR(100),
    website VARCHAR(255),
    contact_email VARCHAR(100),
    contact_number VARCHAR(15)
);

CREATE TABLE Skills (
    skill_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(100)
);

CREATE TABLE Student_Skills (
    student_id INT,
    skill_id INT,
    proficiency_level VARCHAR(50),
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id)
);

CREATE TABLE Opportunity (
    opportunity_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    type ENUM('internship', 'job') NOT NULL,
    posted_date DATE,
    deadline DATE,
    salary DECIMAL(10,2),
    location VARCHAR(100),
    requirements TEXT,
    FOREIGN KEY (company_id) REFERENCES Company(company_id)
);

CREATE TABLE Opportunity_Skills (
    opportunity_id INT,
    skill_id INT,
    is_required BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (opportunity_id, skill_id),
    FOREIGN KEY (opportunity_id) REFERENCES Opportunity(opportunity_id),
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id)
);

CREATE TABLE Application (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    opportunity_id INT,
    application_date DATE,
    status ENUM('applied', 'shortlisted', 'rejected', 'hired') DEFAULT 'applied',
    remarks TEXT,
    FOREIGN KEY (student_id) REFERENCES Student(student_id),
    FOREIGN KEY (opportunity_id) REFERENCES Opportunity(opportunity_id)
);

CREATE TABLE Interview (
    interview_id INT PRIMARY KEY AUTO_INCREMENT,
    application_id INT,
    schedule_date DATETIME,
    venue VARCHAR(255),
    interviewer VARCHAR(100),
    feedback TEXT,
    result ENUM('pending', 'selected', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (application_id) REFERENCES Application(application_id)
);

-- Insert Sample Data for Testing

-- Sample Departments
INSERT INTO Department (name, hod) VALUES 
('Computer Science', 'Dr. Smith'),
('Electrical Engineering', 'Dr. Johnson'),
('Mechanical Engineering', 'Dr. Williams'),
('Civil Engineering', 'Dr. Brown'),
('Information Technology', 'Dr. Davis');

-- Sample Skills
INSERT INTO Skills (name, category) VALUES
('Python', 'Programming'),
('Java', 'Programming'),
('C++', 'Programming'),
('JavaScript', 'Web Development'),
('React', 'Web Development'),
('Angular', 'Web Development'),
('Machine Learning', 'Data Science'),
('Data Analysis', 'Data Science'),
('Networking', 'IT Infrastructure'),
('Database Management', 'IT Infrastructure'),
('AutoCAD', 'Design'),
('SolidWorks', 'Design');

-- Sample Companies
INSERT INTO Company (name, description, industry, website, contact_email, contact_number) VALUES
('TechCorp', 'Leading technology solutions provider', 'Information Technology', 'www.techcorp.com', 'hr@techcorp.com', '1234567890'),
('DataAnalytics Inc', 'Specializing in data analytics and insights', 'Data Analytics', 'www.dataanalytics.com', 'careers@dataanalytics.com', '9876543210'),
('BuildWell Construction', 'Infrastructure and construction company', 'Construction', 'www.buildwell.com', 'jobs@buildwell.com', '5678901234'),
('Innovate Solutions', 'Innovation-driven software development', 'Software Development', 'www.innovatesolutions.com', 'talent@innovatesolutions.com', '8901234567'),
('EnergyTech', 'Renewable energy solutions', 'Energy', 'www.energytech.com', 'recruiting@energytech.com', '3456789012');

-- Sample Opportunities
INSERT INTO Opportunity (company_id, title, description, type, posted_date, deadline, salary, location, requirements) VALUES
(1, 'Software Developer', 'Develop and maintain software applications', 'job', '2023-04-01', '2023-05-15', 800000, 'Bangalore', 'Bachelor's degree in Computer Science or related field. Proficiency in Python and JavaScript.'),
(2, 'Data Analyst', 'Analyze data and create insights', 'job', '2023-04-05', '2023-05-20', 750000, 'Hyderabad', 'Strong analytical skills. Experience with SQL and data visualization tools.'),
(3, 'Civil Engineer', 'Design and oversee construction projects', 'job', '2023-04-10', '2023-05-25', 700000, 'Mumbai', 'Bachelor's degree in Civil Engineering. Knowledge of AutoCAD.'),
(4, 'Frontend Developer Intern', 'Develop user interfaces for web applications', 'internship', '2023-04-15', '2023-05-30', 25000, 'Pune', 'Knowledge of HTML, CSS, and JavaScript. Familiarity with React is a plus.'),
(5, 'Renewable Energy Researcher', 'Conduct research on renewable energy solutions', 'internship', '2023-04-20', '2023-06-05', 20000, 'Chennai', 'Background in Electrical or Mechanical Engineering. Interest in renewable energy.');

-- Sample Opportunity Skills
INSERT INTO Opportunity_Skills (opportunity_id, skill_id, is_required) VALUES
(1, 1, TRUE),  -- Software Developer needs Python
(1, 4, TRUE),  -- Software Developer needs JavaScript
(2, 8, TRUE),  -- Data Analyst needs Data Analysis
(3, 11, TRUE), -- Civil Engineer needs AutoCAD
(4, 4, TRUE),  -- Frontend Developer Intern needs JavaScript
(4, 5, FALSE); -- Frontend Developer Intern optionally needs React 